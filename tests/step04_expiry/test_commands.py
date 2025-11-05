"""Step 04: EXPIRE/TTLコマンドとPassive Expiry統合のテスト

このテストは、04-expiry.mdで実装するEXPIRE/TTLコマンドとPassive Expiryの統合を検証します。

テスト内容:
- EXPIRE: 有効期限の設定
- TTL: 残り有効期限の取得
- Passive Expiry統合: GET/INCRコマンドでの期限切れチェック

講義資料: docs/lectures/04-expiry.md (パート2: EXPIRE/TTLコマンドの実装)
実行方法: pytest tests/step04_expiry/test_commands.py -v
"""

import time

import pytest

from mini_redis.commands import CommandError, CommandHandler
from mini_redis.expiry import ExpiryManager
from mini_redis.storage import DataStore


class TestStep04ExpireCommand:
    """Step 04: EXPIREコマンドのテスト."""

    @pytest.mark.asyncio
    async def test_expire_sets_expiry_for_existing_key(self) -> None:
        """存在するキーに有効期限を設定することを検証.

        検証内容:
        1. Passive Expiry
        2. キーの存在チェック
        3. expiry.set_expiry(key, seconds)
        4. 1を返す（Integer型）
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "value1")

        result = await handler.execute_expire("key1", 10)

        assert result == 1
        # 有効期限が設定されていることを確認
        assert store.get_expiry("key1") is not None

    @pytest.mark.asyncio
    async def test_expire_returns_0_for_nonexistent_key(self) -> None:
        """存在しないキーに対して0を返すことを検証.

        検証内容:
        - キーが存在しない → 0を返す
        - 有効期限は設定されない
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        result = await handler.execute_expire("nonexistent", 10)

        assert result == 0

    @pytest.mark.asyncio
    async def test_expire_returns_0_for_expired_key(self) -> None:
        """期限切れのキーに対して0を返すことを検証.

        検証内容:
        - Passive Expiryで削除される
        - 0を返す（キーが存在しない）
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "value1")
        # 既に期限切れ
        store.set_expiry("key1", int(time.time()) - 1)

        result = await handler.execute_expire("key1", 10)

        assert result == 0
        # キーが削除されている
        assert store.exists("key1") is False

    @pytest.mark.asyncio
    async def test_expire_raises_error_for_negative_seconds(self) -> None:
        """負の秒数に対してCommandErrorをraiseすることを検証.

        検証内容:
        - seconds < 0 → CommandError
        - エラーメッセージの確認
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "value1")

        with pytest.raises(CommandError, match="invalid expire time"):
            await handler.execute_expire("key1", -1)

    @pytest.mark.asyncio
    async def test_expire_raises_error_for_non_integer_seconds(self) -> None:
        """整数でない秒数に対してCommandErrorをraiseすることを検証.

        検証内容:
        - int(args[1])がValueError
        - CommandError("ERR value is not an integer or out of range")
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "value1")

        with pytest.raises(CommandError, match="not an integer"):
            await handler.execute_expire("key1", "not_a_number")  # type: ignore

    @pytest.mark.asyncio
    async def test_expire_updates_existing_expiry(self) -> None:
        """既存の有効期限を更新できることを検証.

        検証内容:
        - 有効期限が既に設定されているキー
        - 新しい有効期限で上書き
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "value1")

        # 最初の有効期限を設定
        await handler.execute_expire("key1", 10)
        first_expiry = store.get_expiry("key1")

        # 有効期限を更新
        time.sleep(0.1)
        await handler.execute_expire("key1", 20)
        second_expiry = store.get_expiry("key1")

        # 2回目の方が後の時刻
        assert second_expiry is not None
        assert first_expiry is not None
        assert second_expiry > first_expiry


class TestStep04TTLCommand:
    """Step 04: TTLコマンドのテスト."""

    @pytest.mark.asyncio
    async def test_ttl_returns_negative_2_for_nonexistent_key(self) -> None:
        """存在しないキーに対して-2を返すことを検証.

        Redis仕様:
        - -2: キーが存在しない
        - -1: キーは存在するが有効期限なし
        - 正の整数: 残り秒数
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        result = await handler.execute_ttl("nonexistent")

        assert result == -2

    @pytest.mark.asyncio
    async def test_ttl_returns_negative_1_for_key_without_expiry(self) -> None:
        """有効期限が設定されていないキーに対して-1を返すことを検証."""
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "value1")

        result = await handler.execute_ttl("key1")

        assert result == -1

    @pytest.mark.asyncio
    async def test_ttl_returns_remaining_seconds(self) -> None:
        """残り有効秒数を返すことを検証.

        検証内容:
        1. Passive Expiry
        2. expiry.get_ttl(key)で残り秒数を取得
        3. expiry_time - current_time
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "value1")
        store.set_expiry("key1", int(time.time()) + 10)

        result = await handler.execute_ttl("key1")

        # 9秒以上10秒以下（タイムラグを考慮）
        assert 9 <= result <= 10

    @pytest.mark.asyncio
    async def test_ttl_returns_negative_2_for_expired_key(self) -> None:
        """期限切れのキーに対して-2を返すことを検証.

        検証内容:
        - Passive Expiryで削除される
        - -2を返す（キーが存在しない）
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "value1")
        # 既に期限切れ
        store.set_expiry("key1", int(time.time()) - 1)

        result = await handler.execute_ttl("key1")

        assert result == -2
        # キーが削除されている
        assert store.exists("key1") is False

    @pytest.mark.asyncio
    async def test_ttl_returns_0_for_key_expiring_now(self) -> None:
        """有効期限が0秒の場合の動作を検証.

        検証内容:
        - 残り時間が0秒またはマイナス → 0を返す（max(0, ttl)）
        - Passive Expiryでは削除されていない場合
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "value1")
        # ほぼ同時刻を設定（まだ削除されていない）
        store.set_expiry("key1", int(time.time()))

        result = await handler.execute_ttl("key1")

        # 0または-2（Passive Expiryで削除された場合）
        assert result in [0, -2]


class TestStep04PassiveExpiryIntegration:
    """Step 04: Passive Expiryの統合テスト（GET/INCRコマンド）."""

    @pytest.mark.asyncio
    async def test_get_returns_none_for_expired_key(self) -> None:
        """GETコマンドが期限切れキーに対してNoneを返すことを検証.

        検証内容:
        - Passive Expiryで削除
        - Noneを返す
        - キーは削除されている
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "value1")
        # 既に期限切れ
        store.set_expiry("key1", int(time.time()) - 1)

        result = await handler.execute_get("key1")

        assert result is None
        # キーが削除されている
        assert store.exists("key1") is False

    @pytest.mark.asyncio
    async def test_get_returns_value_for_valid_key(self) -> None:
        """GETコマンドが有効期限内のキーの値を返すことを検証.

        検証内容:
        - Passive Expiryチェックを通過
        - 値を返す
        - キーは削除されない
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "value1")
        # 10秒後に期限切れ
        store.set_expiry("key1", int(time.time()) + 10)

        result = await handler.execute_get("key1")

        assert result == "value1"
        assert store.exists("key1") is True

    @pytest.mark.asyncio
    async def test_incr_starts_from_1_for_expired_key(self) -> None:
        """INCRコマンドが期限切れキーに対して1を返すことを検証.

        検証内容:
        - Passive Expiryで削除
        - 0から開始（新しいキーとして扱う）
        - 1を返す
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("counter", "5")
        # 既に期限切れ
        store.set_expiry("counter", int(time.time()) - 1)

        result = await handler.execute_incr("counter")

        assert result == 1
        assert store.get("counter") == "1"

    @pytest.mark.asyncio
    async def test_incr_increments_valid_key(self) -> None:
        """INCRコマンドが有効期限内のキーをインクリメントすることを検証.

        検証内容:
        - Passive Expiryチェックを通過
        - 値をインクリメント
        - キーは削除されない
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("counter", "5")
        # 10秒後に期限切れ
        store.set_expiry("counter", int(time.time()) + 10)

        result = await handler.execute_incr("counter")

        assert result == 6
        assert store.get("counter") == "6"
        assert store.exists("counter") is True

    @pytest.mark.asyncio
    async def test_expire_then_get_behavior(self) -> None:
        """EXPIREで設定した有効期限がGETで正しく機能することを検証.

        統合テスト:
        1. キーを設定
        2. EXPIREで有効期限を設定
        3. GETで値を取得（期限内）
        4. 期限切れ後にGET（Noneが返る）
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        # キーを設定
        await handler.execute_set("key1", "value1")

        # 1秒の有効期限を設定
        await handler.execute_expire("key1", 1)

        # 期限内にGET（値が返る）
        result1 = await handler.execute_get("key1")
        assert result1 == "value1"

        # 期限切れまで待機
        time.sleep(1.1)

        # 期限切れ後にGET（Noneが返る）
        result2 = await handler.execute_get("key1")
        assert result2 is None
