"""Step 04: 有効期限管理のテスト

このテストは、04-expiry.mdで実装する2段階有効期限管理を検証します。

テスト内容:
- Passive Expiry: コマンド実行時の期限チェックと削除
- Active Expiry: バックグラウンドでのランダムサンプリングと削除

講義資料: docs/lectures/04-expiry.md
実行方法: pytest tests/step04_expiry/ -v
"""

import time

import pytest

from mini_redis.expiry import ExpiryManager
from mini_redis.storage import DataStore


class TestStep04PassiveExpiry:
    """Step 04: Passive Expiry（受動的期限管理）のテスト."""

    def test_check_and_remove_expired_returns_false_for_nonexistent_key(self) -> None:
        """存在しないキーに対してFalseを返すことを検証.

        検証内容:
        - storage.get_expiry(key)がNone
        - Falseを返す
        - キーは削除されない
        """
        store = DataStore()
        expiry = ExpiryManager(store)

        result = expiry.check_and_remove_expired("nonexistent")

        assert result is False

    def test_check_and_remove_expired_returns_false_for_key_without_expiry(self) -> None:
        """有効期限が設定されていないキーに対してFalseを返すことを検証.

        検証内容:
        - expiry_at = None（有効期限未設定）
        - Falseを返す
        - キーは削除されない
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        store.set("key1", "value1")

        result = expiry.check_and_remove_expired("key1")

        assert result is False
        assert store.exists("key1") is True

    def test_check_and_remove_expired_returns_false_for_valid_key(self) -> None:
        """有効期限内のキーに対してFalseを返すことを検証.

        検証内容:
        - current_time < expiry_time
        - Falseを返す
        - キーは削除されない
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        store.set("key1", "value1")
        # 10秒後に期限切れ
        store.set_expiry("key1", time.time() + 10)

        result = expiry.check_and_remove_expired("key1")

        assert result is False
        assert store.exists("key1") is True

    def test_check_and_remove_expired_removes_expired_key(self) -> None:
        """期限切れのキーを削除してTrueを返すことを検証.

        検証内容:
        - current_time >= expiry_time
        - storage.delete(key)で削除
        - Trueを返す
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        store.set("key1", "value1")
        # 過去の時刻を設定（既に期限切れ）
        store.set_expiry("key1", time.time() - 1)

        result = expiry.check_and_remove_expired("key1")

        assert result is True
        assert store.exists("key1") is False

    def test_check_and_remove_expired_at_exact_expiry_time(self) -> None:
        """有効期限ちょうどのキーは期限切れとして削除されることを検証.

        検証内容:
        - current_time == expiry_time のケース
        - 境界値テスト
        - 削除される（>= 判定）
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        store.set("key1", "value1")
        # 現在時刻を有効期限に設定
        expiry_time = time.time()
        store.set_expiry("key1", expiry_time)

        # わずかに時間を進める
        time.sleep(0.01)
        result = expiry.check_and_remove_expired("key1")

        assert result is True
        assert store.exists("key1") is False


class TestStep04ActiveExpiry:
    """Step 04: Active Expiry（能動的期限管理）のテスト."""

    @pytest.mark.asyncio
    async def test_active_expiry_removes_expired_keys(self) -> None:
        """Active Expiryが期限切れキーを削除することを検証.

        検証内容:
        - _active_expiry_cycle()の1サイクル実行
        - 期限切れキーは削除される
        - 有効なキーは残る
        """
        store = DataStore()
        expiry = ExpiryManager(store)

        # 5つのキーを作成（3つは期限切れ、2つは有効）
        store.set("expired1", "value1")
        store.set_expiry("expired1", time.time() - 1)

        store.set("expired2", "value2")
        store.set_expiry("expired2", time.time() - 1)

        store.set("expired3", "value3")
        store.set_expiry("expired3", time.time() - 1)

        store.set("valid1", "value4")
        store.set_expiry("valid1", time.time() + 100)

        store.set("valid2", "value5")
        store.set_expiry("valid2", time.time() + 100)

        # Active expiryサイクルを1回実行
        await expiry._active_expiry_cycle()

        # 期限切れキーが削除され、有効なキーは残る
        assert store.exists("expired1") is False
        assert store.exists("expired2") is False
        assert store.exists("expired3") is False
        assert store.exists("valid1") is True
        assert store.exists("valid2") is True

    @pytest.mark.asyncio
    async def test_active_expiry_continues_when_deletion_rate_high(self) -> None:
        """削除率が25%を超える場合、ループを継続することを検証.

        検証内容:
        - 削除率 > 25% → 即座に再サンプリング
        - すべての期限切れキーが削除されるまで継続
        - 削除率 <= 25% → ループ終了

        アルゴリズム:
        1. ランダムに20キーをサンプリング
        2. 期限切れキーを削除
        3. 削除率を計算
        4. 削除率 > 25% → ステップ1に戻る
        5. 削除率 <= 25% → 終了
        """
        store = DataStore()
        expiry = ExpiryManager(store)

        # 30キーを作成（すべて期限切れ）
        for i in range(30):
            key = f"key{i}"
            store.set(key, f"value{i}")
            store.set_expiry(key, time.time() - 1)

        # Active expiryサイクルを1回実行
        # 削除率が25%を超えるため、すべてのキーが削除されるまでループが続く
        await expiry._active_expiry_cycle()

        # すべての期限切れキーが削除される
        remaining_keys = len(store.get_all_keys())
        assert remaining_keys == 0

    @pytest.mark.asyncio
    async def test_active_expiry_handles_empty_store(self) -> None:
        """Active Expiryは空のストアでもエラーにならないことを検証.

        検証内容:
        - get_keys_with_expiry()が空リスト
        - 即座に終了
        - エラーは発生しない
        """
        store = DataStore()
        expiry = ExpiryManager(store)

        # 空のストアでActive expiryサイクルを実行
        await expiry._active_expiry_cycle()

        # エラーが発生しないことを確認
        assert len(store.get_all_keys()) == 0

    @pytest.mark.asyncio
    async def test_active_expiry_ignores_keys_without_expiry(self) -> None:
        """Active Expiryは有効期限のないキーを無視することを検証.

        検証内容:
        - get_keys_with_expiry()は有効期限付きキーのみ返す
        - 有効期限のないキーはサンプリング対象外
        - 削除されない
        """
        store = DataStore()
        expiry = ExpiryManager(store)

        # 有効期限のないキーを作成
        store.set("key1", "value1")
        store.set("key2", "value2")

        # Active expiryサイクルを実行
        await expiry._active_expiry_cycle()

        # キーは削除されない
        assert store.exists("key1") is True
        assert store.exists("key2") is True
