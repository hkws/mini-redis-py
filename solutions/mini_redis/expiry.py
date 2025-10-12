"""Expiry management for Mini-Redis keys.

このモジュールは、キーの有効期限管理（Passive + Active expiration）を担当します。
"""

import asyncio
import logging
import random
import time

from .storage import DataStore

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

    def __init__(self, store: DataStore) -> None:
        """マネージャを初期化.

        Args:
            store: データストアのインスタンス
        """
        self._store = store
        self._task: asyncio.Task[None] | None = None
        self._running = False

    def check_and_remove_expired(self, key: str) -> bool:
        """Passive expiry: キーが期限切れかチェックし、期限切れなら削除.

        Args:
            key: チェックするキー

        Returns:
            True: キーが期限切れで削除された
            False: キーは有効または存在しない

        実装のヒント:
        1. キーが存在しない場合はFalseを返す
        2. 有効期限が設定されていない場合はFalseを返す
        3. time.time()で現在時刻を取得し、expiry_atと比較
        4. 期限切れの場合はself._store.delete(key)で削除してTrueを返す
        """
        # 1. キーが存在しない場合はFalseを返す
        if not self._store.exists(key):
            return False

        # 2. 有効期限が設定されていない場合はFalseを返す
        expiry_at = self._store.get_expiry(key)
        if expiry_at is None:
            return False

        # 3. 現在時刻と比較
        current_time = time.time()
        if current_time < expiry_at:
            # まだ有効期限内
            return False

        # 4. 期限切れの場合は削除
        self._store.delete(key)
        return True

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
                await asyncio.sleep(1)
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
            # 全キーを取得
            all_keys = self._store.get_all_keys()

            # キーが存在しない場合は終了
            if not all_keys:
                break

            # 最大ACTIVE_EXPIRY_SAMPLE_SIZEキーをサンプリング
            sample_size = min(ACTIVE_EXPIRY_SAMPLE_SIZE, len(all_keys))
            sampled_keys = random.sample(all_keys, sample_size)

            # 各キーに対して期限チェックと削除を実行
            deleted_count = sum(
                1 for key in sampled_keys if self.check_and_remove_expired(key)
            )

            # 削除率を計算し、しきい値以下ならループを抜ける
            deletion_rate = (deleted_count / sample_size) * 100
            if deletion_rate <= ACTIVE_EXPIRY_THRESHOLD_PERCENT:
                break
