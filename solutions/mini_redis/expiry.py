"""Expiry management for Mini-Redis keys.

このモジュールは、キーの有効期限管理（Passive + Active expiration）を担当します。

"""

import asyncio
import logging
import random
import time

# NOTE: DataStoreは別ファイルで定義されています
# from mini_redis.storage import DataStore

logger = logging.getLogger(__name__)

# Active expiryの定数
ACTIVE_EXPIRY_SAMPLE_SIZE = 20  # 1サイクルでサンプリングする最大キー数
ACTIVE_EXPIRY_THRESHOLD_PERCENT = 25  # 削除率のしきい値（%）


class ExpiryManager:
    """キーの有効期限管理.

    責務:
    - Passive expiry: キーアクセス時に期限をチェックして削除
    - Active expiry: バックグラウンドタスクで定期的に期限切れキーを削除

    ライフサイクル:
    1. __init__(store): インスタンスを作成
    2. start(): Active expiryバックグラウンドタスクを開始
    3. stop(): Active expiryタスクを停止

    主要メソッド:
    - check_and_remove_expired(key): 単一キーの期限チェック（Passive）
    - start(): Active expiryタスクを開始
    - stop(): Active expiryタスクを停止
    """

    def __init__(self, store) -> None:
        """マネージャを初期化.

        Args:
            store: DataStoreのインスタンス

        """
        self._store = store
        self._task: asyncio.Task[None] | None = None
        self._running = False

    def check_and_remove_expired(self, key: str) -> bool:
        """
        キーが期限切れかチェックし、期限切れなら削除する

        Args:
            key: チェックするキー

        Returns:
            True: 期限切れで削除した
            False: 期限内または期限未設定
        """
        # 有効期限を取得
        expiry_time = self._store.get_expiry(key)

        if expiry_time is None:
            # 有効期限が設定されていない
            return False

        # 現在時刻と比較
        current_time = int(time.time())

        if current_time >= expiry_time:
            # 期限切れ: キーを削除
            self._store.delete(key)
            return True

        # 期限内
        return False

    async def start(self) -> None:
        """Active expiryタスクを開始.

        バックグラウンドでactive expiryタスクを起動する。
        stop()が呼ばれるまで実行を継続する。

        Raises:
            RuntimeError: 既に実行中の場合
        """
        if self._running:
            raise RuntimeError("Active expiry is already running")

        logger.info("Starting active expiry task")
        self._running = True
        self._task = asyncio.create_task(self._run_active_expiry())

    async def stop(self) -> None:
        """Active expiryタスクを停止.

        実行中のactive expiryタスクを停止し、完了を待つ。
        タスクが実行中でない場合は何もしない。
        """
        if not self._running:
            return

        logger.info("Stopping active expiry task...")
        self._running = False

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                logger.info("Active expiry task stopped")

        self._task = None

    async def _run_active_expiry(self) -> None:
        """内部: Active expiryのメインループ.

        _runningフラグがTrueの間、1秒ごとにActive expiryサイクルを実行する。
        """
        try:
            logger.info("Active expiry task started")

            while self._running:
                # 1秒待機
                await asyncio.sleep(1)

                # サンプリングと削除を実行
                await self._active_expiry_cycle()

        except asyncio.CancelledError:
            logger.info("Active expiry task cancelled")
            raise

        finally:
            logger.info("Active expiry task finished")

    async def _active_expiry_cycle(self) -> None:
        """1サイクルのActive expiry処理.

        最大ACTIVE_EXPIRY_SAMPLE_SIZEキーをランダムサンプリングし、期限切れキーを削除する。
        削除率がACTIVE_EXPIRY_THRESHOLD_PERCENT%を超える場合、即座に次のサンプリングを実行する。
        """
        while True:
            # すべてのキーを取得
            all_keys = self._store.get_all_keys()

            if not all_keys:
                # キーが存在しない
                break

            # ランダムに最大20個サンプリング
            sample_size = min(ACTIVE_EXPIRY_SAMPLE_SIZE, len(all_keys))
            sampled_keys = random.sample(all_keys, sample_size)

            # 期限切れキーを削除
            deleted_count = sum(
                1 for key in sampled_keys if self.check_and_remove_expired(key)
            )

            # 削除率を計算
            deletion_rate = (deleted_count / sample_size) * 100

            # 削除率が25%以下なら終了
            if deletion_rate <= ACTIVE_EXPIRY_THRESHOLD_PERCENT:
                break

            # 削除率が25%超なら再実行（即座に次のサンプリング）

    def set_expiry(self, key: str, seconds: int) -> None:
        expiry_time = int(time.time()) + seconds
        self._store.set_expiry(key, expiry_time)

    def get_ttl(self, key: str) -> int | None:
        expiry_time = self._store.get_expiry(key)
        if expiry_time is None:
            return None
        return max(0, expiry_time - int(time.time()))
