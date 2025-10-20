"""Step 01: TCPサーバとasyncio - エコーサーバーのテスト

このテストは、01-tcp-server.mdで実装するエコーサーバーの動作を検証します。

テスト内容:
- 単一行のデータのエコーバック
- 複数行のデータのエコーバック
- 各種RESP形式のデータのエコーバック
- クライアント切断時の適切なクリーンアップ

講義資料: docs/lectures/01-tcp-server.md
実行方法: pytest tests/step01_tcp_server/ -v
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
        self._protocol: asyncio.Protocol | None = None

    def write(self, data: bytes) -> None:
        """データをバッファに書き込む."""
        self.buffer.extend(data)

    def is_closing(self) -> bool:
        """接続が閉じられているかを返す."""
        return self._is_closing

    def close(self) -> None:
        """接続を閉じる."""
        self._is_closing = True
        if self._protocol is not None:
            self._protocol.connection_lost(None)

    def get_extra_info(self, name: str, default=None) -> tuple[str, int] | None:
        """接続情報を返す."""
        if name == "peername":
            return ("127.0.0.1", 12345)
        return default

    def set_protocol(self, protocol: asyncio.Protocol) -> None:
        """接続しているプロトコルを登録する."""
        self._protocol = protocol


def create_mock_streams() -> tuple[asyncio.StreamReader, asyncio.StreamWriter, MockTransport]:
    """テスト用のStreamReaderとStreamWriterのペアを作成.

    Returns:
        (reader, writer, transport)のタプル
    """
    reader = asyncio.StreamReader()
    transport = MockTransport()
    protocol = asyncio.StreamReaderProtocol(reader)
    transport.set_protocol(protocol)
    writer = asyncio.StreamWriter(transport, protocol, reader, asyncio.get_event_loop())
    return reader, writer, transport


class TestStep01EchoServer:
    """Step 01: エコーサーバーの動作テスト."""

    @pytest.mark.asyncio
    async def test_echo_single_line(self) -> None:
        """単一行のデータが正しくエコーバックされることを確認.

        検証内容:
        - reader.readuntil(b'\\r\\n')で1行読み取り
        - writer.write()でそのままエコーバック
        - writer.drain()で送信完了
        """
        # モックのストリームを作成
        reader, writer, transport = create_mock_streams()

        # 依存関係を準備（完成版を使用）
        parser = RESPParser()
        store = DataStore()
        expiry = ExpiryManager(store)
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # 1行のデータを送信（RESP Array形式のPINGコマンド）
        data = b"*1\r\n$4\r\nPING\r\n"
        reader.feed_data(data)
        reader.feed_eof()

        # ハンドラを実行（EOFで終了）
        await client_handler.handle(reader, writer)

        # 応答を検証（同じデータがエコーバックされる）
        response = bytes(transport.buffer)
        assert response == data, f"Expected {data!r}, got {response!r}"

    @pytest.mark.asyncio
    async def test_echo_multiple_lines(self) -> None:
        """複数行のデータが順次エコーバックされることを確認.

        検証内容:
        - while Trueループで複数行を処理
        - 各行が順番にエコーバックされる
        """
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
        expected = line1 + line2 + line3
        assert response == expected, f"Expected {expected!r}, got {response!r}"

    @pytest.mark.asyncio
    async def test_handle_client_immediate_disconnect(self) -> None:
        """クライアントが即座に切断したときに正しくクリーンアップされることを確認.

        検証内容:
        - asyncio.IncompleteReadErrorのキャッチ
        - finally句でwriter.close()が呼ばれる
        - writer.wait_closed()でクリーンアップ完了を待つ
        """
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
        assert transport.is_closing(), "Transport should be closed after disconnect"

    @pytest.mark.asyncio
    async def test_handle_partial_line_then_disconnect(self) -> None:
        """不完全な行を受信後に切断した場合の処理を確認.

        検証内容:
        - reader.readuntil()でasyncio.IncompleteReadErrorが発生
        - エラーハンドリングで適切にループを抜ける
        - finally句でクリーンアップが実行される
        """
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
        assert transport.is_closing(), "Transport should be closed after incomplete read"

    @pytest.mark.asyncio
    async def test_echo_various_resp_types(self) -> None:
        """各種RESP形式のデータがエコーバックされることを確認.

        検証内容:
        - Simple String (+OK\\r\\n)
        - Integer (:1000\\r\\n)
        - Error (-ERR\\r\\n)
        - Array header (*2\\r\\n)
        それぞれが正しくエコーバックされる
        """
        test_cases = [
            (b"+OK\r\n", "Simple String"),
            (b":1000\r\n", "Integer"),
            (b"-ERR unknown command\r\n", "Error"),
            (b"*2\r\n", "Array header"),
        ]

        for data, description in test_cases:
            reader, writer, transport = create_mock_streams()

            parser = RESPParser()
            store = DataStore()
            expiry = ExpiryManager(store)
            handler = CommandHandler(store, expiry)
            client_handler = ClientHandler(parser, handler)

            reader.feed_data(data)
            reader.feed_eof()

            await client_handler.handle(reader, writer)

            response = bytes(transport.buffer)
            assert response == data, f"{description}: Expected {data!r}, got {response!r}"
