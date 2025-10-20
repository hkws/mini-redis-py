"""TCP server and client handler for Mini-Redis.

このモジュールは、TCPサーバの起動と管理、
および個別クライアント接続の処理を担当します。

【実装順序のガイド】
1. ClientHandler.handle() - クライアント接続の処理ループ
   - コマンドの読み取り→パース→実行→応答
   - 結果の型判定とエンコード
   - エラーハンドリング

注意: TCPServer.start()とstop()は実装済みです。
     ClientHandler.handle()のみ実装してください。
"""

import asyncio
import logging
from asyncio import StreamReader, StreamWriter
from typing import TYPE_CHECKING

from mini_redis.commands import CommandHandler, CommandError
from mini_redis.protocol import RESPParser, RESPProtocolError

if TYPE_CHECKING:
    from mini_redis.expiry import ExpiryManager
    from mini_redis.storage import DataStore

logger = logging.getLogger(__name__)


class TCPServer:
    """Mini-RedisのTCPサーバ.

    責務:
    - TCP接続の受け入れ
    - クライアントセッションの管理
    - サーバのライフサイクル管理
    - Active Expiryバックグラウンドタスクの管理

    注意: このクラスは実装済みです。変更する必要はありません。
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6379,
        store: "DataStore | None" = None,
        expiry: "ExpiryManager | None" = None,
        client_handler: "ClientHandler | None" = None,
    ) -> None:
        """サーバを初期化.

        Args:
            host: バインドするホスト
            port: バインドするポート
            store: データストア（Noneの場合は新規作成）
            expiry: Expiryマネージャ（Noneの場合は新規作成）
            client_handler: クライアントハンドラ（Noneの場合は新規作成）
        """
        self.host = host
        self.port = port
        self._server: asyncio.Server | None = None
        self._store = store
        self._expiry = expiry
        self._client_handler = client_handler

    async def start(self) -> None:
        """サーバを起動し、接続を待ち受ける.

        Active Expiryバックグラウンドタスクを起動し、TCPサーバを開始する。
        このメソッドはserve_forever()内で無限ループするため、
        KeyboardInterruptや例外が発生するまで戻らない。

        注意: このメソッドは実装済みです。変更する必要はありません。
        """
        # 依存性の初期化（未指定の場合は新規作成）
        from mini_redis.expiry import ExpiryManager
        from mini_redis.storage import DataStore

        store = self._store if self._store is not None else DataStore()
        expiry = self._expiry if self._expiry is not None else ExpiryManager(store)
        # stop()で停止できるように保持
        self._expiry = expiry

        if self._client_handler is not None:
            client_handler = self._client_handler
        else:
            # デフォルトの ClientHandler を作成
            parser = RESPParser()
            handler = CommandHandler(store, expiry)
            client_handler = ClientHandler(parser, handler)

        # 1. asyncio.start_server()でサーバを起動
        self._server = await asyncio.start_server(
            client_handler.handle, self.host, self.port
        )

        addr = self._server.sockets[0].getsockname() if self._server.sockets else (self.host, self.port)
        logger.info(f"Mini-Redis server started on {addr[0]}:{addr[1]}")

        # 2. Active Expiryを開始（バックグラウンドタスク）
        await expiry.start()

        # 3. サーバを実行（無限ループ）
        async with self._server:
            await self._server.serve_forever()

    async def stop(self) -> None:
        """サーバを停止し、すべての接続をクローズする.

        Active Expiryタスクを停止し、TCPサーバをクローズする。

        注意: このメソッドは実装済みです。変更する必要はありません。
        """
        logger.info("Stopping Mini-Redis server...")

        # 1. Active Expiryを停止
        if self._expiry is not None:
            await self._expiry.stop()

        # 2. TCPサーバを停止
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()

        logger.info("Mini-Redis server stopped")


class ClientHandler:
    """クライアント接続のハンドラ.

    責務:
    - 個別クライアントとの通信ループ
    - リクエスト受信→レスポンス送信

    実装のヒント:
    1. handle()メソッドを実装する
    2. 無限ループでコマンドを処理
    3. 結果の型に応じてエンコード
    4. エラーハンドリング
    """

    def __init__(self, parser: RESPParser, handler: CommandHandler) -> None:
        """ハンドラを初期化.

        Args:
            parser: RESPパーサのインスタンス
            handler: コマンドハンドラのインスタンス

        【実装ステップ】
        1. self._parser = parser
        2. self._handler = handler
        """
        self._parser = parser
        self._handler = handler

    async def handle(self, reader: StreamReader, writer: StreamWriter) -> None:
        """クライアント接続を処理するメインループ.

        Args:
            reader: asyncioのStreamReader
            writer: asyncioのStreamWriter
        """
        pass
