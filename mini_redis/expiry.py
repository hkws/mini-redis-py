"""Expiry management for Mini-Redis keys.

このモジュールは、キーの有効期限管理（Passive + Active expiration）を担当します。
"""

import asyncio
import random
import time

from mini_redis.storage import DataStore


class ExpiryManager:
    """キーの有効期限管理.

    責務:
    - Passive expiry: キーアクセス時に期限をチェックして削除
    - Active expiry: バックグラウンドタスクで定期的に期限切れキーを削除

    実装のヒント:
    1. check_and_remove_expired(): 単一キーの期限チェック（Passive）
    2. start_active_expiry(): バックグラウンドタスクを起動（Active）
    3. _active_expiry_cycle(): ランダムサンプリングで期限切れキーを削除
    """

    def __init__(self, store: DataStore) -> None:
        """マネージャを初期化.

        Args:
            store: データストアのインスタンス
        """
        self._store = store

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

    async def start_active_expiry(self) -> None:
        """Active expiry: バックグラウンドタスクを開始.

        実装のヒント:
        1. 無限ループでwhile True
        2. await asyncio.sleep(1)で1秒待機
        3. _active_expiry_cycle()を呼び出し

        このメソッドはサーバ起動時にTaskGroupで起動される
        """
        # TODO: Active expiryのバックグラウンドタスクを実装
        raise NotImplementedError("start_active_expiry() is not implemented yet")

    async def _active_expiry_cycle(self) -> None:
        """1サイクルのActive expiry処理.

        実装のヒント:
        1. self._store.get_all_keys()で全キーを取得
        2. random.sample()で最大20キーをサンプリング
        3. 各キーに対してcheck_and_remove_expired()を呼び出し
        4. 削除されたキーの数をカウント
        5. 削除率 > 25%の場合、ループを継続（即座に次のサンプリング）

        削除率の計算:
        削除率 = (削除されたキー数 / サンプルキー数) * 100
        """
        # TODO: Active expiryのサイクル処理を実装
        raise NotImplementedError("_active_expiry_cycle() is not implemented yet")
