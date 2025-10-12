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

from mini_redis.commands import CommandHandler
from mini_redis.protocol import RESPParser

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

        【実装ステップ】
        ステップ1: クライアント情報を取得してログ出力
        ──────────────────────────────────────
        1. writer.get_extra_info("peername")でクライアントのアドレスを取得
        2. logger.info(f"Client connected: {addr}")でログ出力

        ステップ2: try-finally-whileループの構造を作成
        ────────────────────────────────────────
        1. tryブロックを作成
        2. finallyブロックでwriter.close()とwriter.wait_closed()を呼び出す
        3. tryブロック内にwhile True:無限ループを作成

        ステップ3: コマンドの読み取りとパース
        ───────────────────────────────
        1. tryブロック内でself._parser.parse_command(reader)を呼び出す
        2. 結果をcommand変数に格納

        ステップ4: コマンドの実行
        ─────────────────────
        1. self._handler.execute(command)を呼び出す
        2. 結果をresult変数に格納

        ステップ5: 結果の型判定とエンコード
        ───────────────────────────
        1. isinstance(result, str)の場合:
           - self._parser.encode_simple_string(result)
        2. isinstance(result, int)の場合:
           - self._parser.encode_integer(result)
        3. それ以外（result is None）の場合:
           - self._parser.encode_bulk_string(None)
        4. エンコード結果をresponse変数に格納

        ステップ6: 応答の送信
        ─────────────────
        1. writer.write(response)で応答を送信
        2. await writer.drain()で送信完了を待つ

        ステップ7: エラーハンドリング
        ─────────────────────
        1. CommandError例外をキャッチ:
           - str(e)でエラーメッセージを取得
           - self._parser.encode_error(error_msg)でエンコード
           - writer.write()とawait writer.drain()で送信
           - ループを継続

        2. RESPProtocolError例外をキャッチ:
           - logger.error()でログ出力
           - breakでループを抜ける

        3. asyncio.IncompleteReadError例外をキャッチ:
           - logger.info()でログ出力（クライアント切断）
           - breakでループを抜ける

        4. asyncio.CancelledError例外をキャッチ:
           - logger.info()でログ出力（サーバシャットダウン）
           - raiseで例外を再送出

        5. Exception例外をキャッチ（予期しないエラー）:
           - logger.error()でログ出力
           - breakでループを抜ける

        【重要な概念】
        - 無限ループでコマンドを処理し続ける
        - 各コマンドの実行は独立している
        - エラーが発生してもサーバは継続（接続は切断）
        - finally句で必ずクリーンアップ

        【よくある間違い】
        ❌ writer.drain()を忘れる → データが送信されない
        ❌ finally句を忘れる → 接続がクローズされない
        ❌ CancelledErrorをraiseし忘れる → グレースフルシャットダウンが動作しない

        【ヒント】
        from mini_redis.commands import CommandError
        from mini_redis.protocol import RESPProtocolError
        をメソッド内でimportすると、循環importを避けられます。

        例:
        >>> # クライアントが接続
        >>> # ループ開始
        >>> # コマンド受信: ["PING"]
        >>> # 実行結果: "PONG"
        >>> # エンコード: b'+PONG\\r\\n'
        >>> # 送信完了
        >>> # 次のコマンドを待つ
        """
        # TODO: ステップ1を実装してください
        # addr = writer.get_extra_info("peername")
        # logger.info(f"Client connected: {addr}")

        # TODO: ステップ2を実装してください
        # try:
        #     while True:
        #         try:
        #             # ステップ3-6をここに実装
        #         except CommandError as e:
        #             # ステップ7-1を実装
        #         except RESPProtocolError as e:
        #             # ステップ7-2を実装
        #         except asyncio.IncompleteReadError:
        #             # ステップ7-3を実装
        #         except asyncio.CancelledError:
        #             # ステップ7-4を実装
        #         except Exception as e:
        #             # ステップ7-5を実装
        # finally:
        #     writer.close()
        #     await writer.wait_closed()
        #     logger.info(f"Connection closed: {addr}")

        raise NotImplementedError("handle()を実装してください")
