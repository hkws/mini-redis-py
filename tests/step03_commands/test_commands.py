"""Step 03: Redisコマンド実装のテスト

このテストは、03-commands.mdで実装する4つの基本コマンドを検証します。

テスト内容:
- コマンドルーティング: execute()から各コマンドメソッドへの振り分け
- PING: 接続確認
- GET: 値取得
- SET: 値設定
- INCR: インクリメント

注意: EXPIRE/TTLコマンドのテストは tests/step04_expiry/test_commands.py で実装します。

講義資料: docs/lectures/03-commands.md (パート2: コマンド実行層)
実行方法: pytest tests/step03_commands/test_commands.py -v
"""

import pytest

from mini_redis.commands import CommandError, CommandHandler
from mini_redis.protocol import BulkString, Integer, SimpleString
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
        handler = CommandHandler(store, None)

        # PINGコマンド
        result = await handler.execute(["PING"])
        assert isinstance(result, SimpleString)
        assert result.value == "PONG"

    @pytest.mark.asyncio
    async def test_execute_handles_lowercase_commands(self) -> None:
        """小文字のコマンドも正しく処理されることを検証.

        検証内容:
        - .upper()で大文字に正規化
        - 大文字小文字を区別しない
        """
        store = DataStore()
        handler = CommandHandler(store, None)

        result = await handler.execute(["ping"])
        assert isinstance(result, SimpleString)
        assert result.value == "PONG"

    @pytest.mark.asyncio
    async def test_execute_raises_error_for_unknown_command(self) -> None:
        """未知のコマンドに対してCommandErrorをraiseすることを検証.

        検証内容:
        - else節で未知のコマンドを処理
        - CommandError("ERR unknown command '{cmd_name}'")
        """
        store = DataStore()
        handler = CommandHandler(store, None)

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
        handler = CommandHandler(store, None)

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
        handler = CommandHandler(store, None)

        result = await handler.execute_ping([])
        assert isinstance(result, SimpleString)
        assert result.value == "PONG"

    @pytest.mark.asyncio
    async def test_ping_str_returns_str(self) -> None:
        """PINGコマンドが引数をそのまま返すことを検証.

        仕様:
        - 引数なし: "PONG"を返す
        - 引数あり: 引数をそのまま返す

        検証内容:
        - 戻り値の型: str
        - Bulk Stringとしてエンコードされる
        """
        store = DataStore()
        handler = CommandHandler(store, None)

        result = await handler.execute_ping(["Hello"])
        assert isinstance(result, BulkString)
        assert result.value == "Hello"


class TestStep03GetCommand:
    """Step 03: GETコマンドのテスト."""

    @pytest.mark.asyncio
    async def test_get_returns_value_for_existing_key(self) -> None:
        """存在するキーの値を返すことを検証.

        検証内容:
        1. storage.get(key)で値を取得
        2. Bulk Stringとしてエンコードされる

        注意: Passive Expiryのチェックは04-expiry.mdで追加します。
        """
        store = DataStore()
        handler = CommandHandler(store, None)
        store.set("key1", "value1")

        result = await handler.execute_get(["key1"])
        assert isinstance(result, BulkString)
        assert result.value == "value1"

    @pytest.mark.asyncio
    async def test_get_returns_none_for_nonexistent_key(self) -> None:
        """存在しないキーに対してNoneを返すことを検証.

        検証内容:
        - storage.get(key)がNone
        - Null Bulk String ($-1\\r\\n)としてエンコードされる
        """
        store = DataStore()
        handler = CommandHandler(store, None)

        result = await handler.execute_get(["nonexistent"])
        assert isinstance(result, BulkString)
        assert result.value is None


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
        handler = CommandHandler(store, None)

        result = await handler.execute_set(["key1", "value1"])
        assert isinstance(result, SimpleString)
        assert result.value == "OK"
        assert store.get("key1") == "value1"

    @pytest.mark.asyncio
    async def test_set_overwrites_existing_value(self) -> None:
        """既存の値を上書きすることを検証.

        検証内容:
        - set()は常に上書き
        - 有効期限もクリアされる（04-expiry.mdで検証）
        """
        store = DataStore()
        handler = CommandHandler(store, None)
        store.set("key1", "old_value")

        result = await handler.execute_set(["key1", "new_value"])
        assert isinstance(result, SimpleString)
        assert result.value == "OK"
        assert store.get("key1") == "new_value"


class TestStep03IncrCommand:
    """Step 03: INCRコマンドのテスト."""

    @pytest.mark.asyncio
    async def test_incr_creates_key_with_1_for_nonexistent_key(self) -> None:
        """存在しないキーに対して1を設定することを検証.

        検証内容:
        1. キーが存在しない → 0から開始
        2. storage.set(key, "1")
        3. 1を返す（Integer型）

        注意: Passive Expiryのチェックは04-expiry.mdで追加します。
        """
        store = DataStore()
        handler = CommandHandler(store, None)

        result = await handler.execute_incr(["counter"])
        assert isinstance(result, Integer)
        assert result.value == 1
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
        handler = CommandHandler(store, None)
        store.set("counter", "5")

        result = await handler.execute_incr(["counter"])
        assert isinstance(result, Integer)
        assert result.value == 6
        assert store.get("counter") == "6"

    @pytest.mark.asyncio
    async def test_incr_raises_error_for_non_integer_value(self) -> None:
        """整数でない値に対してCommandErrorをraiseすることを検証.

        検証内容:
        - try-except ValueError
        - CommandError("ERR value is not an integer or out of range")
        """
        store = DataStore()
        handler = CommandHandler(store, None)
        store.set("key1", "not_an_integer")

        with pytest.raises(CommandError, match="not an integer"):
            await handler.execute_incr(["key1"])
