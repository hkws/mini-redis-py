"""Tests for CommandHandler."""

import pytest

from mini_redis.commands import CommandError, CommandHandler
from mini_redis.expiry import ExpiryManager
from mini_redis.storage import DataStore


class TestCommandRouting:
    """コマンドルーティングのテスト."""

    @pytest.mark.asyncio
    async def test_execute_routes_to_correct_method(self) -> None:
        """コマンド名から適切なメソッドにルーティングされる."""
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        # PINGコマンド
        result = await handler.execute(["PING"])
        assert result == "PONG"

    @pytest.mark.asyncio
    async def test_execute_handles_lowercase_commands(self) -> None:
        """小文字のコマンドも正しく処理される."""
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        result = await handler.execute(["ping"])
        assert result == "PONG"

    @pytest.mark.asyncio
    async def test_execute_raises_error_for_unknown_command(self) -> None:
        """未知のコマンドに対してCommandErrorをraiseする."""
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        with pytest.raises(CommandError, match="unknown command"):
            await handler.execute(["UNKNOWNCOMMAND"])

    @pytest.mark.asyncio
    async def test_execute_raises_error_for_wrong_number_of_args(self) -> None:
        """引数の数が不正な場合にCommandErrorをraiseする."""
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        # GETは引数が1つ必要
        with pytest.raises(CommandError, match="wrong number of arguments"):
            await handler.execute(["GET"])


class TestPingCommand:
    """PINGコマンドのテスト."""

    @pytest.mark.asyncio
    async def test_ping_returns_pong(self) -> None:
        """PINGコマンドは常にPONGを返す."""
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        result = await handler.execute_ping()
        assert result == "PONG"


class TestGetCommand:
    """GETコマンドのテスト."""

    @pytest.mark.asyncio
    async def test_get_returns_value_for_existing_key(self) -> None:
        """存在するキーの値を返す."""
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "value1")

        result = await handler.execute_get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_returns_none_for_nonexistent_key(self) -> None:
        """存在しないキーに対してNoneを返す."""
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        result = await handler.execute_get("nonexistent")
        assert result is None


class TestSetCommand:
    """SETコマンドのテスト."""

    @pytest.mark.asyncio
    async def test_set_stores_value(self) -> None:
        """キーに値を保存する."""
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        result = await handler.execute_set("key1", "value1")
        assert result == "OK"
        assert store.get("key1") == "value1"

    @pytest.mark.asyncio
    async def test_set_overwrites_existing_value(self) -> None:
        """既存の値を上書きする."""
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "old_value")

        result = await handler.execute_set("key1", "new_value")
        assert result == "OK"
        assert store.get("key1") == "new_value"


class TestIncrCommand:
    """INCRコマンドのテスト."""

    @pytest.mark.asyncio
    async def test_incr_creates_key_with_1_for_nonexistent_key(self) -> None:
        """存在しないキーに対して1を設定する."""
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        result = await handler.execute_incr("counter")
        assert result == 1
        assert store.get("counter") == "1"

    @pytest.mark.asyncio
    async def test_incr_increments_existing_integer_value(self) -> None:
        """既存の整数値を1増加させる."""
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("counter", "5")

        result = await handler.execute_incr("counter")
        assert result == 6
        assert store.get("counter") == "6"

    @pytest.mark.asyncio
    async def test_incr_raises_error_for_non_integer_value(self) -> None:
        """整数でない値に対してCommandErrorをraiseする."""
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "not_an_integer")

        with pytest.raises(CommandError, match="not an integer"):
            await handler.execute_incr("key1")


class TestExpireCommand:
    """EXPIREコマンドのテスト."""

    @pytest.mark.asyncio
    async def test_expire_sets_expiry_for_existing_key(self) -> None:
        """存在するキーに有効期限を設定する."""
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "value1")

        result = await handler.execute_expire("key1", 10)
        assert result == 1
        assert store.get_expiry("key1") is not None

    @pytest.mark.asyncio
    async def test_expire_returns_0_for_nonexistent_key(self) -> None:
        """存在しないキーに対して0を返す."""
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        result = await handler.execute_expire("nonexistent", 10)
        assert result == 0


class TestTtlCommand:
    """TTLコマンドのテスト."""

    @pytest.mark.asyncio
    async def test_ttl_returns_negative_2_for_nonexistent_key(self) -> None:
        """存在しないキーに対して-2を返す."""
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        result = await handler.execute_ttl("nonexistent")
        assert result == -2

    @pytest.mark.asyncio
    async def test_ttl_returns_negative_1_for_key_without_expiry(self) -> None:
        """有効期限が設定されていないキーに対して-1を返す."""
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "value1")

        result = await handler.execute_ttl("key1")
        assert result == -1

    @pytest.mark.asyncio
    async def test_ttl_returns_remaining_seconds(self) -> None:
        """残り有効秒数を返す."""
        import time

        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "value1")
        store.set_expiry("key1", time.time() + 10)

        result = await handler.execute_ttl("key1")
        # 9秒以上10秒以下（タイムラグを考慮）
        assert 9 <= result <= 10
