"""Step 02: RESPプロトコルのパースとエンコード - テスト

このテストは、02-protocol-parsing.mdで実装するRESPプロトコルの
パーサーとエンコーダーの動作を検証します。

テスト内容:
- エンコード: Simple String, Error, Integer, Bulk String
- パース: 各種コマンド形式（PING, GET, SET, INCR, EXPIRE, TTL）
- エラーハンドリング: 不正な形式の処理

講義資料: docs/lectures/02-protocol-parsing.md
実行方法: pytest tests/step02_protocol/ -v
"""

import asyncio

import pytest

from mini_redis.protocol import RESPParser, RESPProtocolError


class TestStep02RESPEncoder:
    """Step 02: RESPエンコーディングのテスト."""

    def test_encode_simple_string(self) -> None:
        """Simple String形式のエンコードを検証.

        形式: +{文字列}\\r\\n

        検証内容:
        - 通常の文字列 ("OK", "PONG")
        - 空文字列
        """
        parser = RESPParser()

        # 正常系: 通常の文字列
        assert parser.encode_simple_string("OK") == b"+OK\r\n"
        assert parser.encode_simple_string("PONG") == b"+PONG\r\n"

        # 空文字列
        assert parser.encode_simple_string("") == b"+\r\n"

    def test_encode_error(self) -> None:
        """Error形式のエンコードを検証.

        形式: -{エラーメッセージ}\\r\\n

        検証内容:
        - 標準的なエラーメッセージ
        - 空のエラーメッセージ
        """
        parser = RESPParser()

        # 正常系: エラーメッセージ
        assert parser.encode_error("ERR unknown command") == b"-ERR unknown command\r\n"
        assert parser.encode_error("ERR wrong number of arguments") == (
            b"-ERR wrong number of arguments\r\n"
        )

        # 空のエラーメッセージ
        assert parser.encode_error("") == b"-\r\n"

    def test_encode_integer(self) -> None:
        """Integer形式のエンコードを検証.

        形式: :{整数}\\r\\n

        検証内容:
        - 正の整数（0, 42, 1000）
        - 負の整数（-1, -42）
        """
        parser = RESPParser()

        # 正常系: 正の整数
        assert parser.encode_integer(0) == b":0\r\n"
        assert parser.encode_integer(42) == b":42\r\n"
        assert parser.encode_integer(1000) == b":1000\r\n"

        # 負の整数
        assert parser.encode_integer(-1) == b":-1\r\n"
        assert parser.encode_integer(-42) == b":-42\r\n"

    def test_encode_bulk_string(self) -> None:
        """Bulk String形式のエンコードを検証.

        形式: ${長さ}\\r\\n{データ}\\r\\n

        検証内容:
        - 通常の文字列（バイト長の計算）
        - 空文字列（$0\\r\\n\\r\\n）
        - Null値（$-1\\r\\n）
        - 改行を含む文字列（バイナリセーフ）
        """
        parser = RESPParser()

        # 正常系: 通常の文字列
        assert parser.encode_bulk_string("foo") == b"$3\r\nfoo\r\n"
        assert parser.encode_bulk_string("hello") == b"$5\r\nhello\r\n"

        # 空文字列
        assert parser.encode_bulk_string("") == b"$0\r\n\r\n"

        # Null Bulk String
        assert parser.encode_bulk_string(None) == b"$-1\r\n"

        # 複数行を含む文字列（バイナリセーフ）
        assert parser.encode_bulk_string("foo\r\nbar") == b"$8\r\nfoo\r\nbar\r\n"

    def test_encode_array(self) -> None:
        """Array形式のエンコードを検証.

        形式: *{要素数}\\r\\n{要素1}{要素2}...

        検証内容:
        - 空配列（*0\\r\\n）
        - Simple Stringの配列
        - Bulk Stringの配列
        - 混合型の配列
        - Null配列（*-1\\r\\n）
        """
        from mini_redis.protocol import SimpleString, BulkString, Integer

        parser = RESPParser()

        # 空配列
        assert parser.encode_array([]) == b"*0\r\n"

        # Simple Stringの配列
        items = [SimpleString("OK"), SimpleString("PONG")]
        expected = b"*2\r\n+OK\r\n+PONG\r\n"
        assert parser.encode_array(items) == expected

        # Bulk Stringの配列
        items = [BulkString("foo"), BulkString("bar"), BulkString("baz")]
        expected = b"*3\r\n$3\r\nfoo\r\n$3\r\nbar\r\n$3\r\nbaz\r\n"
        assert parser.encode_array(items) == expected

        # 混合型の配列（Simple String, Bulk String, Integer）
        items = [SimpleString("OK"), BulkString("hello"), Integer(42)]
        expected = b"*3\r\n+OK\r\n$5\r\nhello\r\n:42\r\n"
        assert parser.encode_array(items) == expected

        # Null Array
        assert parser.encode_array(None) == b"*-1\r\n"

    def test_encode_response(self) -> None:
        """encode_responseで各型が適切にエンコードされることを検証.

        検証内容:
        - SimpleString型
        - RedisError型
        - Integer型
        - BulkString型
        - Array型
        - サポートされていない型でエラー
        """
        from mini_redis.protocol import SimpleString, RedisError, Integer, BulkString, Array

        parser = RESPParser()

        # SimpleString
        result = SimpleString("OK")
        assert parser.encode_response(result) == b"+OK\r\n"

        # RedisError
        result = RedisError("ERR unknown command")
        assert parser.encode_response(result) == b"-ERR unknown command\r\n"

        # Integer
        result = Integer(42)
        assert parser.encode_response(result) == b":42\r\n"

        # BulkString
        result = BulkString("hello")
        assert parser.encode_response(result) == b"$5\r\nhello\r\n"

        # BulkString (Null)
        result = BulkString(None)
        assert parser.encode_response(result) == b"$-1\r\n"

        # Array
        result = Array([SimpleString("OK"), Integer(1)])
        assert parser.encode_response(result) == b"*2\r\n+OK\r\n:1\r\n"

        # サポートされていない型
        with pytest.raises(ValueError) as exc_info:
            parser.encode_response("invalid")
        assert "Unsupported type" in str(exc_info.value)


class TestStep02RESPParser:
    """Step 02: RESPパーシングのテスト."""

    @pytest.mark.asyncio
    async def test_parse_ping_command(self) -> None:
        """PINGコマンドのパースを検証.

        RESP形式: *1\\r\\n$4\\r\\nPING\\r\\n

        パース手順:
        1. 配列ヘッダー (*1) を読む → 要素数1
        2. Bulk String ($4\\r\\nPING\\r\\n) を読む → "PING"
        3. 結果: ["PING"]
        """
        parser = RESPParser()

        data = b"*1\r\n$4\r\nPING\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        result = await parser.parse_command(reader)
        assert result == ["PING"], f"Expected ['PING'], got {result}"

    @pytest.mark.asyncio
    async def test_parse_get_command(self) -> None:
        """GETコマンドのパースを検証.

        RESP形式: *2\\r\\n$3\\r\\nGET\\r\\n$3\\r\\nfoo\\r\\n

        パース手順:
        1. 配列ヘッダー (*2) → 要素数2
        2. Bulk String 1: "GET"
        3. Bulk String 2: "foo"
        4. 結果: ["GET", "foo"]
        """
        parser = RESPParser()

        data = b"*2\r\n$3\r\nGET\r\n$3\r\nfoo\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        result = await parser.parse_command(reader)
        assert result == ["GET", "foo"], f"Expected ['GET', 'foo'], got {result}"

    @pytest.mark.asyncio
    async def test_parse_set_command(self) -> None:
        """SETコマンドのパースを検証.

        RESP形式: *3\\r\\n$3\\r\\nSET\\r\\n$3\\r\\nkey\\r\\n$5\\r\\nvalue\\r\\n

        パース手順:
        1. 配列ヘッダー (*3) → 要素数3
        2. Bulk String 1: "SET"
        3. Bulk String 2: "key"
        4. Bulk String 3: "value"
        5. 結果: ["SET", "key", "value"]
        """
        parser = RESPParser()

        data = b"*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        result = await parser.parse_command(reader)
        assert result == ["SET", "key", "value"]

    @pytest.mark.asyncio
    async def test_parse_command_with_empty_string(self) -> None:
        """空文字列を含むコマンドのパースを検証.

        RESP形式: *3\\r\\n$3\\r\\nSET\\r\\n$3\\r\\nkey\\r\\n$0\\r\\n\\r\\n

        検証内容:
        - 空文字列のBulk String ($0\\r\\n\\r\\n)
        - 結果: ["SET", "key", ""]
        """
        parser = RESPParser()

        data = b"*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$0\r\n\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        result = await parser.parse_command(reader)
        assert result == ["SET", "key", ""]

    @pytest.mark.asyncio
    async def test_parse_incr_command(self) -> None:
        """INCRコマンドのパースを検証.

        RESP形式: *2\\r\\n$4\\r\\nINCR\\r\\n$7\\r\\ncounter\\r\\n
        """
        parser = RESPParser()

        data = b"*2\r\n$4\r\nINCR\r\n$7\r\ncounter\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        result = await parser.parse_command(reader)
        assert result == ["INCR", "counter"]

    @pytest.mark.asyncio
    async def test_parse_expire_command(self) -> None:
        """EXPIREコマンドのパースを検証.

        RESP形式: *3\\r\\n$6\\r\\nEXPIRE\\r\\n$5\\r\\nmykey\\r\\n$2\\r\\n60\\r\\n

        検証内容:
        - コマンド名: "EXPIRE"
        - キー: "mykey"
        - 秒数（文字列として）: "60"
        """
        parser = RESPParser()

        data = b"*3\r\n$6\r\nEXPIRE\r\n$5\r\nmykey\r\n$2\r\n60\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        result = await parser.parse_command(reader)
        assert result == ["EXPIRE", "mykey", "60"]

    @pytest.mark.asyncio
    async def test_parse_ttl_command(self) -> None:
        """TTLコマンドのパースを検証.

        RESP形式: *2\\r\\n$3\\r\\nTTL\\r\\n$5\\r\\nmykey\\r\\n
        """
        parser = RESPParser()

        data = b"*2\r\n$3\r\nTTL\r\n$5\r\nmykey\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        result = await parser.parse_command(reader)
        assert result == ["TTL", "mykey"]

    @pytest.mark.asyncio
    async def test_parse_multiple_commands_sequentially(self) -> None:
        """複数のコマンドを順次パースできることを検証.

        検証内容:
        - PING, GET, INCR, EXPIRE, TTLコマンド
        - それぞれが正しくパースされる
        """
        parser = RESPParser()

        commands = [
            (b"*1\r\n$4\r\nPING\r\n", ["PING"]),
            (b"*2\r\n$3\r\nGET\r\n$3\r\nfoo\r\n", ["GET", "foo"]),
            (b"*2\r\n$4\r\nINCR\r\n$7\r\ncounter\r\n", ["INCR", "counter"]),
            (b"*3\r\n$6\r\nEXPIRE\r\n$3\r\nkey\r\n$2\r\n10\r\n", ["EXPIRE", "key", "10"]),
            (b"*2\r\n$3\r\nTTL\r\n$3\r\nkey\r\n", ["TTL", "key"]),
        ]

        for data, expected in commands:
            reader = asyncio.StreamReader()
            reader.feed_data(data)
            reader.feed_eof()

            result = await parser.parse_command(reader)
            assert result == expected


class TestStep02RESPProtocolErrors:
    """Step 02: RESPプロトコルエラーハンドリングのテスト."""

    @pytest.mark.asyncio
    async def test_invalid_array_prefix(self) -> None:
        """不正な配列プレフィックスのエラーハンドリング.

        検証内容:
        - *以外で始まるデータ → RESPProtocolError
        """
        parser = RESPParser()

        data = b"+INVALID\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        with pytest.raises(RESPProtocolError):
            await parser.parse_command(reader)

    @pytest.mark.asyncio
    async def test_invalid_bulk_string_prefix(self) -> None:
        """不正なBulk Stringプレフィックスのエラーハンドリング.

        検証内容:
        - 配列の要素が$で始まらない → RESPProtocolError
        """
        parser = RESPParser()

        data = b"*1\r\n+INVALID\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        with pytest.raises(RESPProtocolError):
            await parser.parse_command(reader)

    @pytest.mark.asyncio
    async def test_invalid_bulk_string_length(self) -> None:
        """不正なBulk String長のエラーハンドリング.

        検証内容:
        - 長さが数値でない → RESPProtocolError
        """
        parser = RESPParser()

        data = b"*1\r\n$ABC\r\nPING\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        with pytest.raises(RESPProtocolError):
            await parser.parse_command(reader)

    @pytest.mark.asyncio
    async def test_incomplete_message(self) -> None:
        """不完全なメッセージのエラーハンドリング.

        検証内容:
        - データが途中で切れている → asyncio.IncompleteReadError
        """
        parser = RESPParser()

        data = b"*1\r\n$4\r\nPI"  # PINGの途中
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        with pytest.raises(asyncio.IncompleteReadError):
            await parser.parse_command(reader)

    @pytest.mark.asyncio
    async def test_length_mismatch(self) -> None:
        """長さとデータの不一致のエラーハンドリング.

        検証内容:
        - Bulk Stringの長さ指定と実際のデータが不一致 → RESPProtocolError
        """
        parser = RESPParser()

        data = b"*1\r\n$4\r\nPINGEXTRA\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        with pytest.raises(RESPProtocolError):
            await parser.parse_command(reader)
