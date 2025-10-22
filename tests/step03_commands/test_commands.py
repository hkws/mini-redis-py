"""Step 03: Redisコマンド実装のテスト

このテストは、03-commands.mdで実装する6つの基本コマンドを検証します。

テスト内容:
- コマンドルーティング: execute()から各コマンドメソッドへの振り分け
- PING: 接続確認
- GET: 値取得
- SET: 値設定
- INCR: インクリメント
- EXPIRE: 有効期限設定
- TTL: 残り有効期限取得

講義資料: docs/lectures/03-commands.md (パート2: コマンド実行層)
実行方法: pytest tests/step03_commands/test_commands.py -v
"""

import pytest

from mini_redis.commands import CommandError, CommandHandler
from mini_redis.expiry import ExpiryManager
from mini_redis.storage import DataStore


class TestStep03CommandRouting:
    """Step 03: コマンドルーティングのテスト."""

    @pytest.mark.asyncio
    async def test_execute_routes_to_correct_method(self) -> None:
        """コマンド名から適切なメソッドにルーティングされることを検証.

        検証内容:
        - command[0].upper()でコマンド名を取得
        - if/elif/elseで適切なメソッドに振り分け
        - 引数（command[1:]）を渡す
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        # PINGコマンド
        result = await handler.execute(["PING"])
        assert result == "PONG"

    @pytest.mark.asyncio
    async def test_execute_handles_lowercase_commands(self) -> None:
        """小文字のコマンドも正しく処理されることを検証.

        検証内容:
        - .upper()で大文字に正規化
        - 大文字小文字を区別しない
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        result = await handler.execute(["ping"])
        assert result == "PONG"

    @pytest.mark.asyncio
    async def test_execute_raises_error_for_unknown_command(self) -> None:
        """未知のコマンドに対してCommandErrorをraiseすることを検証.

        検証内容:
        - else節で未知のコマンドを処理
        - CommandError("ERR unknown command '{cmd_name}'")
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        with pytest.raises(CommandError, match="unknown command"):
            await handler.execute(["UNKNOWNCOMMAND"])

    @pytest.mark.asyncio
    async def test_execute_raises_error_for_wrong_number_of_args(self) -> None:
        """引数の数が不正な場合にCommandErrorをraiseすることを検証.

        検証内容:
        - 各コマンドメソッド内で引数数をチェック
        - CommandError("ERR wrong number of arguments...")
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        # GETは引数が1つ必要
        with pytest.raises(CommandError, match="wrong number of arguments"):
            await handler.execute(["GET"])


class TestStep03PingCommand:
    """Step 03: PINGコマンドのテスト."""

    @pytest.mark.asyncio
    async def test_ping_returns_pong(self) -> None:
        """PINGコマンドがPONGを返すことを検証.

        仕様:
        - 引数なし: "PONG"を返す
        - 引数あり: 引数をそのまま返す

        検証内容:
        - 戻り値の型: str
        - Simple Stringとしてエンコードされる
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        result = await handler.execute_ping([])
        assert result == "PONG"


class TestStep03GetCommand:
    """Step 03: GETコマンドのテスト."""

    @pytest.mark.asyncio
    async def test_get_returns_value_for_existing_key(self) -> None:
        """存在するキーの値を返すことを検証.

        検証内容:
        1. Passive Expiry: check_and_remove_expired()
        2. storage.get(key)で値を取得
        3. Bulk Stringとしてエンコードされる
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "value1")

        result = await handler.execute_get(["key1"])
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_returns_none_for_nonexistent_key(self) -> None:
        """存在しないキーに対してNoneを返すことを検証.

        検証内容:
        - storage.get(key)がNone
        - Null Bulk String ($-1\\r\\n)としてエンコードされる
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        result = await handler.execute_get(["nonexistent"])
        assert result is None


class TestStep03SetCommand:
    """Step 03: SETコマンドのテスト."""

    @pytest.mark.asyncio
    async def test_set_stores_value(self) -> None:
        """キーに値を保存することを検証.

        検証内容:
        1. storage.set(key, value)で保存
        2. "OK"を返す
        3. Simple Stringとしてエンコードされる
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        result = await handler.execute_set(["key1", "value1"])
        assert result == "OK"
        assert store.get("key1") == "value1"

    @pytest.mark.asyncio
    async def test_set_overwrites_existing_value(self) -> None:
        """既存の値を上書きすることを検証.

        検証内容:
        - set()は常に上書き
        - 有効期限もクリアされる
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "old_value")

        result = await handler.execute_set(["key1", "new_value"])
        assert result == "OK"
        assert store.get("key1") == "new_value"


class TestStep03IncrCommand:
    """Step 03: INCRコマンドのテスト."""

    @pytest.mark.asyncio
    async def test_incr_creates_key_with_1_for_nonexistent_key(self) -> None:
        """存在しないキーに対して1を設定することを検証.

        検証内容:
        1. Passive Expiry
        2. キーが存在しない → 0から開始
        3. storage.set(key, "1")
        4. 1を返す（Integer型）
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)

        result = await handler.execute_incr(["counter"])
        assert result == 1
        assert store.get("counter") == "1"

    @pytest.mark.asyncio
    async def test_incr_increments_existing_integer_value(self) -> None:
        """既存の整数値を1増加させることを検証.

        検証内容:
        1. int(current_value)で整数に変換
        2. value + 1
        3. storage.set(key, str(new_value))
        4. new_valueを返す（Integer型）
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("counter", "5")

        result = await handler.execute_incr(["counter"])
        assert result == 6
        assert store.get("counter") == "6"

    @pytest.mark.asyncio
    async def test_incr_raises_error_for_non_integer_value(self) -> None:
        """整数でない値に対してCommandErrorをraiseすることを検証.

        検証内容:
        - try-except ValueError
        - CommandError("ERR value is not an integer or out of range")
        """
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "not_an_integer")

        with pytest.raises(CommandError, match="not an integer"):
            await handler.execute_incr(["key1"])


class TestStep03ExpireCommand:
    """Step 03: EXPIREコマンドのテスト."""

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

        result = await handler.execute_expire(["key1", 10])
        assert result == 1
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

        result = await handler.execute_expire(["nonexistent", 10])
        assert result == 0


class TestStep03TtlCommand:
    """Step 03: TTLコマンドのテスト."""

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

        result = await handler.execute_ttl(["nonexistent"])
        assert result == -2

    @pytest.mark.asyncio
    async def test_ttl_returns_negative_1_for_key_without_expiry(self) -> None:
        """有効期限が設定されていないキーに対して-1を返すことを検証."""
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "value1")

        result = await handler.execute_ttl(["key1"])
        assert result == -1

    @pytest.mark.asyncio
    async def test_ttl_returns_remaining_seconds(self) -> None:
        """残り有効秒数を返すことを検証.

        検証内容:
        1. Passive Expiry
        2. expiry.get_ttl(key)で残り秒数を取得
        3. expiry_time - current_time
        """
        import time

        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        store.set("key1", "value1")
        store.set_expiry("key1", time.time() + 10)

        result = await handler.execute_ttl(["key1"])
        # 9秒以上10秒以下（タイムラグを考慮）
        assert 9 <= result <= 10
