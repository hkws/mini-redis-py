"""Tests for ClientHandler.

ClientHandler.handle()メソッドに焦点を当てたテストスイート。
TCPServerは実装済みのため、テスト対象外。
"""

import asyncio

import pytest

# 他のコンポーネントは完成版を使用
from solutions.mini_redis.commands import CommandHandler
from solutions.mini_redis.expiry import ExpiryManager
from solutions.mini_redis.protocol import RESPParser
from solutions.mini_redis.storage import DataStore

# テスト対象のみmini_redisからimport
from mini_redis.server import ClientHandler


class MockTransport:
    """テスト用のモックTransport.

    StreamWriterに渡すデータをキャプチャするために使用します。
    """

    def __init__(self) -> None:
        """モックTransportを初期化."""
        self.buffer = bytearray()
        self._is_closing = False

    def write(self, data: bytes) -> None:
        """データをバッファに書き込む."""
        self.buffer.extend(data)

    def is_closing(self) -> bool:
        """接続が閉じられているかを返す."""
        return self._is_closing

    def close(self) -> None:
        """接続を閉じる."""
        self._is_closing = True

    def get_extra_info(self, name: str, default=None) -> tuple[str, int] | None:
        """接続情報を返す."""
        if name == "peername":
            return ("127.0.0.1", 12345)
        return default


def create_mock_streams() -> tuple[asyncio.StreamReader, asyncio.StreamWriter, MockTransport]:
    """テスト用のStreamReaderとStreamWriterのペアを作成.

    Returns:
        (reader, writer, transport)のタプル
    """
    reader = asyncio.StreamReader()
    transport = MockTransport()
    protocol = asyncio.StreamReaderProtocol(asyncio.StreamReader())
    writer = asyncio.StreamWriter(transport, protocol, reader, asyncio.get_event_loop())
    return reader, writer, transport


class TestClientHandler:
    """ClientHandler.handle()メソッドのテスト."""

    @pytest.mark.asyncio
    async def test_handle_ping_command(self) -> None:
        """PINGコマンドを正しく処理する."""
        # モックのストリームを作成
        reader, writer, transport = create_mock_streams()

        # 依存関係を準備
        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # PINGコマンドをRESP形式で送信
        ping_command = b"*1\r\n$4\r\nPING\r\n"
        reader.feed_data(ping_command)
        reader.feed_eof()

        # ハンドラを実行（EOFで終了）
        await client_handler.handle(reader, writer)

        # 応答を検証
        response = bytes(transport.buffer)
        assert response == b"+PONG\r\n"

    @pytest.mark.asyncio
    async def test_handle_multiple_commands(self) -> None:
        """複数のコマンドを順次処理する."""
        reader, writer, transport = create_mock_streams()

        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # 複数のコマンドを送信（PING、SET、GET）
        commands = (
            b"*1\r\n$4\r\nPING\r\n"
            b"*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"
            b"*2\r\n$3\r\nGET\r\n$3\r\nfoo\r\n"
        )
        reader.feed_data(commands)
        reader.feed_eof()

        # ハンドラを実行
        await client_handler.handle(reader, writer)

        # 応答を検証（PONG + OK + bar）
        response = bytes(transport.buffer)
        assert response == b"+PONG\r\n+OK\r\n$3\r\nbar\r\n"

    @pytest.mark.asyncio
    async def test_handle_set_get_commands(self) -> None:
        """SET/GETコマンドの基本動作を確認."""
        reader, writer, transport = create_mock_streams()

        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # SET key value → GET key
        commands = (
            b"*3\r\n$3\r\nSET\r\n$4\r\nname\r\n$5\r\nAlice\r\n"
            b"*2\r\n$3\r\nGET\r\n$4\r\nname\r\n"
        )
        reader.feed_data(commands)
        reader.feed_eof()

        await client_handler.handle(reader, writer)

        # 応答を検証（OK + Alice）
        response = bytes(transport.buffer)
        assert response == b"+OK\r\n$5\r\nAlice\r\n"

    @pytest.mark.asyncio
    async def test_handle_get_nonexistent_key(self) -> None:
        """存在しないキーのGETでnullが返ることを確認."""
        reader, writer, transport = create_mock_streams()

        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # 存在しないキーをGET
        command = b"*2\r\n$3\r\nGET\r\n$7\r\nmissing\r\n"
        reader.feed_data(command)
        reader.feed_eof()

        await client_handler.handle(reader, writer)

        # 応答を検証（null bulk string）
        response = bytes(transport.buffer)
        assert response == b"$-1\r\n"

    @pytest.mark.asyncio
    async def test_handle_del_command(self) -> None:
        """DELコマンドで削除された数が返ることを確認."""
        reader, writer, transport = create_mock_streams()

        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # SET key value → DEL key
        commands = (
            b"*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$3\r\nval\r\n"
            b"*2\r\n$3\r\nDEL\r\n$3\r\nkey\r\n"
        )
        reader.feed_data(commands)
        reader.feed_eof()

        await client_handler.handle(reader, writer)

        # 応答を検証（OK + 1）
        response = bytes(transport.buffer)
        assert response == b"+OK\r\n:1\r\n"

    @pytest.mark.asyncio
    async def test_handle_incr_command(self) -> None:
        """INCRコマンドで整数値がインクリメントされることを確認."""
        reader, writer, transport = create_mock_streams()

        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # SET counter 10 → INCR counter
        commands = (
            b"*3\r\n$3\r\nSET\r\n$7\r\ncounter\r\n$2\r\n10\r\n"
            b"*2\r\n$4\r\nINCR\r\n$7\r\ncounter\r\n"
        )
        reader.feed_data(commands)
        reader.feed_eof()

        await client_handler.handle(reader, writer)

        # 応答を検証（OK + 11）
        response = bytes(transport.buffer)
        assert response == b"+OK\r\n:11\r\n"

    @pytest.mark.asyncio
    async def test_handle_unknown_command_error(self) -> None:
        """不正なコマンドを送信してエラーが返ることを確認."""
        reader, writer, transport = create_mock_streams()

        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # 存在しないコマンド
        invalid_command = b"*1\r\n$7\r\nINVALID\r\n"
        reader.feed_data(invalid_command)
        reader.feed_eof()

        await client_handler.handle(reader, writer)

        # エラーレスポンスを検証
        response = bytes(transport.buffer)
        assert response.startswith(b"-ERR")

    @pytest.mark.asyncio
    async def test_handle_incr_non_integer_error(self) -> None:
        """INCRコマンドで非整数値を持つキーを操作してエラーが返ることを確認."""
        reader, writer, transport = create_mock_streams()

        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # キーに文字列をセット→INCRで操作
        commands = (
            b"*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nhello\r\n"  # SET key hello
            b"*2\r\n$4\r\nINCR\r\n$3\r\nkey\r\n"  # INCR key
        )
        reader.feed_data(commands)
        reader.feed_eof()

        await client_handler.handle(reader, writer)

        # 応答を検証（OK + エラー）
        response = bytes(transport.buffer)
        assert b"+OK\r\n" in response
        assert b"-ERR" in response

    @pytest.mark.asyncio
    async def test_handle_wrong_number_of_args_error(self) -> None:
        """引数の数が間違っているコマンドでエラーが返ることを確認."""
        reader, writer, transport = create_mock_streams()

        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # SETコマンドに引数が足りない（keyのみでvalueなし）
        command = b"*2\r\n$3\r\nSET\r\n$3\r\nkey\r\n"
        reader.feed_data(command)
        reader.feed_eof()

        await client_handler.handle(reader, writer)

        # エラーレスポンスを検証
        response = bytes(transport.buffer)
        assert b"-ERR" in response

    @pytest.mark.asyncio
    async def test_handle_client_immediate_disconnect(self) -> None:
        """クライアントが即座に切断したときに正しくクリーンアップされることを確認."""
        reader, writer, transport = create_mock_streams()

        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # コマンドを送信せずにEOFを送る（即座に切断）
        reader.feed_eof()

        # ハンドラを実行（エラーなく終了するべき）
        await client_handler.handle(reader, writer)

        # writerが閉じられていることを確認
        assert transport.is_closing()

    @pytest.mark.asyncio
    async def test_handle_partial_command_then_disconnect(self) -> None:
        """不完全なコマンドを受信後に切断した場合の処理を確認."""
        reader, writer, transport = create_mock_streams()

        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # 不完全なコマンド（配列のサイズのみ）
        partial_command = b"*3\r\n$3\r\nSET\r\n"
        reader.feed_data(partial_command)
        reader.feed_eof()  # 途中でEOF

        # ハンドラを実行（エラーログが出るが、正常終了するべき）
        await client_handler.handle(reader, writer)

        # writerが閉じられていることを確認
        assert transport.is_closing()

    @pytest.mark.asyncio
    async def test_handle_exists_command(self) -> None:
        """EXISTSコマンドが正しく動作することを確認."""
        reader, writer, transport = create_mock_streams()

        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # SET key → EXISTS key → EXISTS missing
        commands = (
            b"*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$3\r\nval\r\n"
            b"*2\r\n$6\r\nEXISTS\r\n$3\r\nkey\r\n"
            b"*2\r\n$6\r\nEXISTS\r\n$7\r\nmissing\r\n"
        )
        reader.feed_data(commands)
        reader.feed_eof()

        await client_handler.handle(reader, writer)

        # 応答を検証（OK + 1 + 0）
        response = bytes(transport.buffer)
        assert response == b"+OK\r\n:1\r\n:0\r\n"
