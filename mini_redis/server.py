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
        # TODO: TCPサーバの起動処理を実装
        raise NotImplementedError("start() is not implemented yet")

    async def stop(self) -> None:
        """サーバを停止し、すべての接続をクローズ.

        実装のヒント:
        1. self._server.close()でサーバを停止
        2. await self._server.wait_closed()で終了を待つ
        """
        # TODO: サーバの停止処理を実装
        raise NotImplementedError("stop() is not implemented yet")


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
        # TODO: クライアント接続の処理ループを実装
        raise NotImplementedError("handle() is not implemented yet")
