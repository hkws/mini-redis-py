"""Tests for RESP protocol parser and encoder."""

import asyncio
from io import BytesIO

import pytest

from mini_redis.protocol import RESPParser, RESPProtocolError


class TestRESPEncoder:
    """Test RESP encoding functions."""

    def test_encode_simple_string(self) -> None:
        """Test encoding simple strings."""
        parser = RESPParser()

        # 正常系: 通常の文字列
        assert parser.encode_simple_string("OK") == b"+OK\r\n"
        assert parser.encode_simple_string("PONG") == b"+PONG\r\n"

        # 空文字列
        assert parser.encode_simple_string("") == b"+\r\n"

    def test_encode_error(self) -> None:
        """Test encoding errors."""
        parser = RESPParser()

        # 正常系: エラーメッセージ
        assert parser.encode_error("ERR unknown command") == b"-ERR unknown command\r\n"
        assert parser.encode_error("ERR wrong number of arguments") == (
            b"-ERR wrong number of arguments\r\n"
        )

        # 空のエラーメッセージ
        assert parser.encode_error("") == b"-\r\n"

    def test_encode_integer(self) -> None:
        """Test encoding integers."""
        parser = RESPParser()

        # 正常系: 正の整数
        assert parser.encode_integer(0) == b":0\r\n"
        assert parser.encode_integer(42) == b":42\r\n"
        assert parser.encode_integer(1000) == b":1000\r\n"

        # 負の整数
        assert parser.encode_integer(-1) == b":-1\r\n"
        assert parser.encode_integer(-42) == b":-42\r\n"

    def test_encode_bulk_string(self) -> None:
        """Test encoding bulk strings."""
        parser = RESPParser()

        # 正常系: 通常の文字列
        assert parser.encode_bulk_string("foo") == b"$3\r\nfoo\r\n"
        assert parser.encode_bulk_string("hello") == b"$5\r\nhello\r\n"

        # 空文字列
        assert parser.encode_bulk_string("") == b"$0\r\n\r\n"

        # Null Bulk String
        assert parser.encode_bulk_string(None) == b"$-1\r\n"

        # 複数行を含む文字列
        assert parser.encode_bulk_string("foo\r\nbar") == b"$8\r\nfoo\r\nbar\r\n"


class TestRESPParser:
    """Test RESP parsing functions."""

    @pytest.mark.asyncio
    async def test_parse_simple_command(self) -> None:
        """Test parsing simple commands like PING."""
        parser = RESPParser()

        # PING コマンド: *1\r\n$4\r\nPING\r\n
        data = b"*1\r\n$4\r\nPING\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        result = await parser.parse_command(reader)
        assert result == ["PING"]

    @pytest.mark.asyncio
    async def test_parse_command_with_arguments(self) -> None:
        """Test parsing commands with arguments."""
        parser = RESPParser()

        # GET foo: *2\r\n$3\r\nGET\r\n$3\r\nfoo\r\n
        data = b"*2\r\n$3\r\nGET\r\n$3\r\nfoo\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        result = await parser.parse_command(reader)
        assert result == ["GET", "foo"]

        # SET key value: *3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n
        data = b"*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        result = await parser.parse_command(reader)
        assert result == ["SET", "key", "value"]

    @pytest.mark.asyncio
    async def test_parse_command_with_empty_string(self) -> None:
        """Test parsing commands with empty string arguments."""
        parser = RESPParser()

        # SET key "": *3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$0\r\n\r\n
        data = b"*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$0\r\n\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        result = await parser.parse_command(reader)
        assert result == ["SET", "key", ""]

    @pytest.mark.asyncio
    async def test_parse_incr_command(self) -> None:
        """Test parsing INCR command."""
        parser = RESPParser()

        # INCR counter: *2\r\n$4\r\nINCR\r\n$7\r\ncounter\r\n
        data = b"*2\r\n$4\r\nINCR\r\n$7\r\ncounter\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        result = await parser.parse_command(reader)
        assert result == ["INCR", "counter"]

    @pytest.mark.asyncio
    async def test_parse_expire_command(self) -> None:
        """Test parsing EXPIRE command."""
        parser = RESPParser()

        # EXPIRE mykey 60: *3\r\n$6\r\nEXPIRE\r\n$5\r\nmykey\r\n$2\r\n60\r\n
        data = b"*3\r\n$6\r\nEXPIRE\r\n$5\r\nmykey\r\n$2\r\n60\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        result = await parser.parse_command(reader)
        assert result == ["EXPIRE", "mykey", "60"]

    @pytest.mark.asyncio
    async def test_parse_ttl_command(self) -> None:
        """Test parsing TTL command."""
        parser = RESPParser()

        # TTL mykey: *2\r\n$3\r\nTTL\r\n$5\r\nmykey\r\n
        data = b"*2\r\n$3\r\nTTL\r\n$5\r\nmykey\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        result = await parser.parse_command(reader)
        assert result == ["TTL", "mykey"]

    @pytest.mark.asyncio
    async def test_parse_multiple_commands_sequentially(self) -> None:
        """Test parsing multiple commands in sequence."""
        parser = RESPParser()

        # 複数のコマンドを順次パース
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


class TestRESPProtocolErrors:
    """Test RESP protocol error handling."""

    @pytest.mark.asyncio
    async def test_invalid_array_prefix(self) -> None:
        """Test handling of invalid array prefix."""
        parser = RESPParser()

        # 不正なプレフィックス（*ではない）
        data = b"+INVALID\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        with pytest.raises(RESPProtocolError):
            await parser.parse_command(reader)

    @pytest.mark.asyncio
    async def test_invalid_bulk_string_prefix(self) -> None:
        """Test handling of invalid bulk string prefix."""
        parser = RESPParser()

        # 配列の要素が$で始まらない
        data = b"*1\r\n+INVALID\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        with pytest.raises(RESPProtocolError):
            await parser.parse_command(reader)

    @pytest.mark.asyncio
    async def test_invalid_bulk_string_length(self) -> None:
        """Test handling of invalid bulk string length."""
        parser = RESPParser()

        # 長さが不正（数値でない）
        data = b"*1\r\n$ABC\r\nPING\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        with pytest.raises(RESPProtocolError):
            await parser.parse_command(reader)

    @pytest.mark.asyncio
    async def test_incomplete_message(self) -> None:
        """Test handling of incomplete messages."""
        parser = RESPParser()

        # 不完全なメッセージ（CRLFが途中で切れる）
        data = b"*1\r\n$4\r\nPI"  # PINGの途中
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        with pytest.raises(asyncio.IncompleteReadError):
            await parser.parse_command(reader)

    @pytest.mark.asyncio
    async def test_length_mismatch(self) -> None:
        """Test handling of length mismatch in bulk strings."""
        parser = RESPParser()

        # 長さとデータが不一致
        data = b"*1\r\n$4\r\nPINGEXTRA\r\n"
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()

        # 長さ4を読み取り、その後\r\nがあることを期待するが、EXTRAが続く
        # この場合、\r\nの検証でエラーが発生するはず
        with pytest.raises(RESPProtocolError):
            await parser.parse_command(reader)
