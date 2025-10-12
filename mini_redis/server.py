"""TCP server and client handler for Mini-Redis.

このモジュールは、TCPサーバの起動と管理、
および個別クライアント接続の処理を担当します。
"""

import asyncio
import logging
from asyncio import StreamReader, StreamWriter

from mini_redis.commands import CommandHandler
from mini_redis.protocol import RESPParser

logger = logging.getLogger(__name__)


class TCPServer:
    """Mini-RedisのTCPサーバ.

    責務:
    - TCP接続の受け入れ
    - クライアントセッションの管理
    - サーバのライフサイクル管理

    実装のヒント:
    1. start(): asyncio.start_server()でサーバを起動
    2. stop(): サーバをシャットダウン
    3. 各クライアント接続にClientHandlerを起動
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 6379) -> None:
        """サーバを初期化.

        Args:
            host: バインドするホスト
            port: バインドするポート
        """
        self.host = host
        self.port = port
        self._server: asyncio.Server | None = None

    async def start(self) -> None:
        """サーバを起動し、接続を待ち受ける.

        実装のヒント:
        1. asyncio.start_server()を使用してサーバを起動
        2. ClientHandler.handle()をコールバックとして指定
        3. Ctrl+Cでのシャットダウンを待つ
        4. 終了時にstop()を呼び出す
        """
        # ClientHandlerのインスタンスを作成
        from mini_redis.expiry import ExpiryManager
        from mini_redis.storage import DataStore

        store = DataStore()
        expiry = ExpiryManager(store)
        parser = RESPParser()
        handler = CommandHandler(store, expiry)
        client_handler = ClientHandler(parser, handler)

        # 1. asyncio.start_server()でサーバを起動
        self._server = await asyncio.start_server(
            client_handler.handle, self.host, self.port
        )

        addr = self._server.sockets[0].getsockname() if self._server.sockets else (self.host, self.port)
        logger.info(f"Mini-Redis server started on {addr[0]}:{addr[1]}")

        # 2. サーバを実行し続ける
        async with self._server:
            await self._server.serve_forever()

    async def stop(self) -> None:
        """サーバを停止し、すべての接続をクローズ.

        実装のヒント:
        1. self._server.close()でサーバを停止
        2. await self._server.wait_closed()で終了を待つ
        """
        if self._server is not None:
            logger.info("Stopping Mini-Redis server...")
            # 1. サーバを停止
            self._server.close()
            # 2. 終了を待つ
            await self._server.wait_closed()
            logger.info("Mini-Redis server stopped")


class ClientHandler:
    """クライアント接続のハンドラ.

    責務:
    - 個別クライアントとの通信ループ
    - リクエスト受信→レスポンス送信

    実装のヒント:
    1. handle(): コマンドの読み取り→パース→実行→応答のループ
    2. 接続切断時の適切なクリーンアップ
    """

    def __init__(self, parser: RESPParser, handler: CommandHandler) -> None:
        """ハンドラを初期化.

        Args:
            parser: RESPパーサのインスタンス
            handler: コマンドハンドラのインスタンス
        """
        self._parser = parser
        self._handler = handler

    async def handle(self, reader: StreamReader, writer: StreamWriter) -> None:
        """クライアント接続を処理するメインループ.

        Args:
            reader: asyncioのStreamReader
            writer: asyncioのStreamWriter

        実装のヒント:
        1. 無限ループでクライアントからのコマンドを待つ
        2. self._parser.parse_command(reader)でコマンドをパース
        3. self._handler.execute(command)でコマンドを実行
        4. 実行結果をRESP形式にエンコード
        5. writer.write()で応答を送信
        6. 接続切断時（EOFError等）はループを抜ける
        7. finally節でwriter.close()を呼び出す
        """
        from mini_redis.commands import CommandError
        from mini_redis.protocol import RESPProtocolError

        addr = writer.get_extra_info("peername")
        logger.info(f"Client connected: {addr}")

        try:
            # 1. 無限ループでコマンドを待つ
            while True:
                try:
                    # 2. コマンドをパース
                    command = await self._parser.parse_command(reader)

                    # 3. コマンドを実行
                    result = await self._handler.execute(command)

                    # 4. 実行結果をRESP形式にエンコード
                    if isinstance(result, str):
                        response = self._parser.encode_simple_string(result)
                    elif isinstance(result, int):
                        response = self._parser.encode_integer(result)
                    else:  # result is None
                        response = self._parser.encode_bulk_string(None)

                    # 5. 応答を送信
                    writer.write(response)
                    await writer.drain()

                except CommandError as e:
                    # コマンドエラーの場合はエラーメッセージを返す
                    error_msg = str(e)
                    response = self._parser.encode_error(error_msg)
                    writer.write(response)
                    await writer.drain()

                except RESPProtocolError as e:
                    # プロトコルエラーの場合はログに記録して接続を切断
                    logger.error(f"RESP protocol error from {addr}: {e}")
                    break

                except asyncio.IncompleteReadError:
                    # 6. 接続が切断された場合はループを抜ける
                    logger.info(f"Client disconnected: {addr}")
                    break

                except Exception as e:
                    # 予期しないエラー
                    logger.error(f"Unexpected error from {addr}: {e}")
                    break

        finally:
            # 7. 接続をクローズ
            writer.close()
            await writer.wait_closed()
            logger.info(f"Connection closed: {addr}")
