"""Tests for ClientHandler (Echo Server version).

ClientHandler.handle()メソッドに焦点を当てたテストスイート。
このバージョンでは、エコーサーバーとしての基本動作のみをテストします。
TCPServerは実装済みのため、テスト対象外。

コマンドのパース・実行・エンコードは次のセクションで実装するため、
このテストでは受信データがそのまま返されることを確認します。
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


class TestClientHandlerEchoServer:
    """ClientHandler.handle()メソッドのテスト（エコーサーバー版）."""

    @pytest.mark.asyncio
    async def test_echo_single_line(self) -> None:
        """1行のデータが正しくエコーバックされることを確認."""
        # モックのストリームを作成
        reader, writer, transport = create_mock_streams()

        # 依存関係を準備
        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # 1行のデータを送信
        data = b"*1\r\n$4\r\nPING\r\n"
        reader.feed_data(data)
        reader.feed_eof()

        # ハンドラを実行（EOFで終了）
        await client_handler.handle(reader, writer)

        # 応答を検証（同じデータがエコーバックされる）
        response = bytes(transport.buffer)
        assert response == data

    @pytest.mark.asyncio
    async def test_echo_multiple_lines(self) -> None:
        """複数行のデータが順次エコーバックされることを確認."""
        reader, writer, transport = create_mock_streams()

        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # 複数行のデータを送信
        line1 = b"*1\r\n$4\r\nPING\r\n"
        line2 = b"*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"
        line3 = b"*2\r\n$3\r\nGET\r\n$3\r\nfoo\r\n"

        reader.feed_data(line1)
        reader.feed_data(line2)
        reader.feed_data(line3)
        reader.feed_eof()

        # ハンドラを実行
        await client_handler.handle(reader, writer)

        # 応答を検証（すべてのデータがエコーバックされる）
        response = bytes(transport.buffer)
        assert response == line1 + line2 + line3

    @pytest.mark.asyncio
    async def test_echo_simple_string(self) -> None:
        """シンプルな文字列がエコーバックされることを確認."""
        reader, writer, transport = create_mock_streams()

        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # RESP Simple String形式のデータ
        data = b"+OK\r\n"
        reader.feed_data(data)
        reader.feed_eof()

        await client_handler.handle(reader, writer)

        # 応答を検証
        response = bytes(transport.buffer)
        assert response == data

    @pytest.mark.asyncio
    async def test_echo_bulk_string(self) -> None:
        """Bulk String形式のデータがエコーバックされることを確認."""
        reader, writer, transport = create_mock_streams()

        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # RESP Bulk String形式のデータ（ただし\r\nで終わる1行のみ）
        data = b"$5\r\nhello\r\n"
        reader.feed_data(data)
        reader.feed_eof()

        await client_handler.handle(reader, writer)

        # 応答を検証
        response = bytes(transport.buffer)
        # エコーサーバーなので、最初の行（$5\r\n）のみがエコーバックされる
        assert response == b"$5\r\n"

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
    async def test_handle_partial_line_then_disconnect(self) -> None:
        """不完全な行を受信後に切断した場合の処理を確認."""
        reader, writer, transport = create_mock_streams()

        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # 不完全な行（\r\nで終わっていない）
        partial_data = b"*3\r\n$3\r\nSET\r\n"
        reader.feed_data(partial_data)
        reader.feed_eof()  # 途中でEOF

        # ハンドラを実行（エラーログが出るが、正常終了するべき）
        await client_handler.handle(reader, writer)

        # writerが閉じられていることを確認
        assert transport.is_closing()

    @pytest.mark.asyncio
    async def test_echo_integer(self) -> None:
        """RESP Integer形式のデータがエコーバックされることを確認."""
        reader, writer, transport = create_mock_streams()

        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # RESP Integer形式のデータ
        data = b":1000\r\n"
        reader.feed_data(data)
        reader.feed_eof()

        await client_handler.handle(reader, writer)

        # 応答を検証
        response = bytes(transport.buffer)
        assert response == data

    @pytest.mark.asyncio
    async def test_echo_error(self) -> None:
        """RESP Error形式のデータがエコーバックされることを確認."""
        reader, writer, transport = create_mock_streams()

        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # RESP Error形式のデータ
        data = b"-ERR unknown command\r\n"
        reader.feed_data(data)
        reader.feed_eof()

        await client_handler.handle(reader, writer)

        # 応答を検証
        response = bytes(transport.buffer)
        assert response == data

    @pytest.mark.asyncio
    async def test_echo_array_header(self) -> None:
        """RESP Array形式のヘッダーがエコーバックされることを確認."""
        reader, writer, transport = create_mock_streams()

        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # RESP Array形式のヘッダー
        data = b"*2\r\n"
        reader.feed_data(data)
        reader.feed_eof()

        await client_handler.handle(reader, writer)

        # 応答を検証
        response = bytes(transport.buffer)
        assert response == data
