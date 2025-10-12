"""Expiry management for Mini-Redis keys.

このモジュールは、キーの有効期限管理（Passive + Active expiration）を担当します。

【実装順序のガイド】
1. check_and_remove_expired() - Passive expiry（シンプル）
2. _active_expiry_cycle() - Active expiryの1サイクル（複雑）
3. _run_active_expiry() - Active expiryのメインループ
4. start() / stop() - タスクの起動・停止

【重要な概念】
- Passive expiry: キーにアクセスした時に期限をチェックして削除
- Active expiry: バックグラウンドで定期的にランダムサンプリングして削除
- 削除率: サンプルしたキーのうち、実際に削除されたキーの割合
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

        【実装ステップ】
        1. self._store = store
        2. self._task: asyncio.Task[None] | None = None（バックグラウンドタスク）
        3. self._running = False（実行状態フラグ）
        """
        # TODO: 実装してください
        raise NotImplementedError("__init__()を実装してください")

    def check_and_remove_expired(self, key: str) -> bool:
        """Passive expiry: キーが期限切れかチェックし、期限切れなら削除.

        Args:
            key: チェックするキー

        Returns:
            True: キーが期限切れで削除された
            False: キーは有効または存在しない

        【実装ステップ】
        ステップ1: キーの存在確認
        ─────────────────────
        1. self._store.exists(key)でキーが存在するか確認
        2. 存在しない場合はFalseを返す

        ステップ2: 有効期限の確認
        ─────────────────────
        1. self._store.get_expiry(key)で有効期限を取得
        2. expiry_atがNoneの場合（有効期限なし）はFalseを返す

        ステップ3: 期限切れチェック
        ──────────────────────
        1. time.time()で現在時刻（Unix timestamp）を取得
        2. current_time < expiry_atの場合（まだ有効期限内）はFalseを返す

        ステップ4: 期限切れキーを削除
        ───────────────────────
        1. self._store.delete(key)でキーを削除
        2. Trueを返す

        【ヒント】
        - time.time(): 現在時刻のUnix timestamp（浮動小数点）
        - 比較: current_time >= expiry_at なら期限切れ

        例:
        >>> # 期限切れキーの場合
        >>> manager.check_and_remove_expired("expired_key")
        True  # 削除された

        >>> # 有効期限内のキーの場合
        >>> manager.check_and_remove_expired("valid_key")
        False  # 削除されなかった

        >>> # 存在しないキーの場合
        >>> manager.check_and_remove_expired("nonexistent")
        False
        """
        # TODO: ステップ1を実装してください
        # if not self._store.exists(key):
        #     return False

        # TODO: ステップ2を実装してください
        # expiry_at = self._store.get_expiry(key)
        # if expiry_at is None:
        #     return False

        # TODO: ステップ3を実装してください
        # current_time = time.time()
        # if current_time < expiry_at:
        #     return False

        # TODO: ステップ4を実装してください
        # self._store.delete(key)
        # return True

        raise NotImplementedError("check_and_remove_expired()を実装してください")

    async def start(self) -> None:
        """Active expiryタスクを開始.

        バックグラウンドでactive expiryタスクを起動する。
        stop()が呼ばれるまで実行を継続する。

        Raises:
            RuntimeError: 既に実行中の場合

        【実装ステップ】
        1. self._runningがTrueの場合、RuntimeError("Active expiry is already running")をraise
        2. logger.info("Starting active expiry task")でログ出力
        3. self._running = Trueを設定
        4. self._task = asyncio.create_task(self._run_active_expiry())でバックグラウンドタスクを起動

        【ヒント】
        asyncio.create_task()は非同期タスクをバックグラウンドで実行します。
        awaitしないため、すぐにメソッドは終了しますが、タスクは実行し続けます。
        """
        # TODO: 実装してください
        raise NotImplementedError("start()を実装してください")

    async def stop(self) -> None:
        """Active expiryタスクを停止.

        実行中のactive expiryタスクを停止し、完了を待つ。
        タスクが実行中でない場合は何もしない。

        【実装ステップ】
        1. self._runningがFalseの場合、何もせずreturn
        2. logger.info("Stopping active expiry task...")でログ出力
        3. self._running = Falseを設定（ループを停止）
        4. self._taskが存在し、完了していない場合:
           - self._task.cancel()でタスクをキャンセル
           - try-exceptでawait self._taskを待つ（CancelledErrorをキャッチ）
           - logger.info("Active expiry task stopped")でログ出力
        5. self._task = Noneをクリア

        【ヒント】
        タスクのキャンセルは以下の手順:
        1. task.cancel()を呼び出す
        2. await taskでCancelledErrorを待つ
        3. CancelledErrorをキャッチして処理
        """
        # TODO: 実装してください
        raise NotImplementedError("stop()を実装してください")

    async def _run_active_expiry(self) -> None:
        """内部: Active expiryのメインループ.

        _runningフラグがTrueの間、1秒ごとにActive expiryサイクルを実行する。

        【実装ステップ】
        1. try-except-finallyブロックを作成
        2. logger.info("Active expiry task started")でログ出力
        3. while self._running:ループ
           - await asyncio.sleep(1)で1秒待機
           - await self._active_expiry_cycle()でサイクル実行
        4. except asyncio.CancelledError:
           - logger.info("Active expiry task cancelled")でログ出力
           - raiseで例外を再送出
        5. finally:
           - logger.info("Active expiry task finished")でログ出力

        【ヒント】
        asyncio.sleep()は非ブロッキングな待機。
        他のタスクがこの間に実行される。

        【注意】
        CancelledErrorは必ずraiseすること！
        でないと、タスクのキャンセルが正しく処理されない。
        """
        # TODO: 実装してください
        raise NotImplementedError("_run_active_expiry()を実装してください")

    async def _active_expiry_cycle(self) -> None:
        """1サイクルのActive expiry処理.

        最大ACTIVE_EXPIRY_SAMPLE_SIZEキーをランダムサンプリングし、期限切れキーを削除する。
        削除率がACTIVE_EXPIRY_THRESHOLD_PERCENT%を超える場合、即座に次のサンプリングを実行する。

        【実装ステップ】
        ステップ1: 無限ループの開始
        ──────────────────────
        1. while True:ループを開始

        ステップ2: 全キーを取得
        ─────────────────
        1. self._store.get_all_keys()ですべてのキーを取得
        2. キーが存在しない場合（空リスト）、breakでループを抜ける

        ステップ3: ランダムサンプリング
        ───────────────────────
        1. sample_size = min(ACTIVE_EXPIRY_SAMPLE_SIZE, len(all_keys))でサンプル数を決定
        2. random.sample(all_keys, sample_size)でランダムにキーをサンプリング

        ステップ4: 期限切れキーを削除
        ───────────────────────
        1. 各キーに対してcheck_and_remove_expired()を呼び出す
        2. 削除されたキーの数をカウント

        ヒント: リスト内包表記とsum()を使うと簡潔:
        deleted_count = sum(1 for key in sampled_keys if self.check_and_remove_expired(key))

        ステップ5: 削除率を計算してループ制御
        ──────────────────────────────
        1. deletion_rate = (deleted_count / sample_size) * 100で削除率を計算
        2. deletion_rate <= ACTIVE_EXPIRY_THRESHOLD_PERCENTの場合、breakでループを抜ける
        3. そうでない場合、whileループの先頭に戻る（次のサンプリング）

        【重要な概念】
        削除率が高い（25%超）= まだ多くの期限切れキーが残っている可能性
        → 即座に次のサンプリングを実行してメモリを解放

        削除率が低い（25%以下）= 期限切れキーが少ない
        → 次の1秒待機まで処理を中断

        【よくある間違い】
        ❌ whileループを使わず1回だけサンプリング → 削除率チェックが機能しない
        ✅ whileループで削除率が低くなるまで繰り返す

        【デバッグのヒント】
        削除率をログ出力すると動作確認に便利:
        logger.debug(f"Active expiry: sampled={sample_size}, deleted={deleted_count}, rate={deletion_rate:.1f}%")

        例:
        サンプル: 20キー
        削除: 8キー
        削除率: 8/20 * 100 = 40% > 25%
        → 再度サンプリング

        サンプル: 20キー
        削除: 3キー
        削除率: 3/20 * 100 = 15% <= 25%
        → ループ終了
        """
        # TODO: ステップ1を実装してください
        # while True:

        # TODO: ステップ2を実装してください
        #     all_keys = self._store.get_all_keys()
        #     if not all_keys:
        #         break

        # TODO: ステップ3を実装してください
        #     sample_size = min(ACTIVE_EXPIRY_SAMPLE_SIZE, len(all_keys))
        #     sampled_keys = random.sample(all_keys, sample_size)

        # TODO: ステップ4を実装してください
        #     deleted_count = sum(
        #         1 for key in sampled_keys if self.check_and_remove_expired(key)
        #     )

        # TODO: ステップ5を実装してください
        #     deletion_rate = (deleted_count / sample_size) * 100
        #     if deletion_rate <= ACTIVE_EXPIRY_THRESHOLD_PERCENT:
        #         break

        raise NotImplementedError("_active_expiry_cycle()を実装してください")
