"""RESP (REdis Serialization Protocol) parser and encoder.

このモジュールは、RESPプロトコルのパース（バイト列→Pythonオブジェクト）と
エンコード（Pythonオブジェクト→バイト列）を担当します。
"""

from asyncio import StreamReader
from typing import Optional


class RESPParser:
    """RESPプロトコルのパーサ・エンコーダ.

    責務:
    - RESPプロトコルのパース（バイト列→Pythonオブジェクト）
    - RESPプロトコルのエンコード（Pythonオブジェクト→バイト列）

    実装のヒント:
    1. parse_command(): StreamReaderから1コマンド分を読み取ってパース
    2. encode_*(): 各RESP型に応じたエンコード関数を実装
    """

    async def parse_command(self, reader: StreamReader) -> list[str]:
        """StreamReaderからRESPコマンドを読み取りパース.

        Args:
            reader: asyncioのStreamReader

        Returns:
            コマンド名と引数のリスト（例: ["GET", "foo"]）

        Raises:
            RESPProtocolError: 不正なRESP形式
            asyncio.IncompleteReadError: 接続が途中で切断

        実装のヒント:
        1. reader.readuntil(b'\\r\\n')で1行ずつ読み取る
        2. 最初の行は "*N\\r\\n" 形式（Nは配列の要素数）
        3. 各要素は "$length\\r\\ndata\\r\\n" 形式のBulk String
        4. lengthバイト分のデータを読み取る
        """
        # TODO: RESPコマンドのパース処理を実装
        raise NotImplementedError("parse_command() is not implemented yet")

    def encode_simple_string(self, value: str) -> bytes:
        """Simple Stringをエンコード.

        Args:
            value: エンコードする文字列

        Returns:
            RESP Simple String形式（例: +OK\\r\\n）

        実装のヒント:
        プレフィックス '+' + 文字列 + '\\r\\n'
        """
        # TODO: Simple Stringのエンコード処理を実装
        raise NotImplementedError("encode_simple_string() is not implemented yet")

    def encode_error(self, message: str) -> bytes:
        """Errorをエンコード.

        Args:
            message: エラーメッセージ

        Returns:
            RESP Error形式（例: -ERR message\\r\\n）

        実装のヒント:
        プレフィックス '-' + メッセージ + '\\r\\n'
        """
        # TODO: Errorのエンコード処理を実装
        raise NotImplementedError("encode_error() is not implemented yet")

    def encode_integer(self, value: int) -> bytes:
        """Integerをエンコード.

        Args:
            value: エンコードする整数

        Returns:
            RESP Integer形式（例: :42\\r\\n）

        実装のヒント:
        プレフィックス ':' + 整数の文字列表現 + '\\r\\n'
        """
        # TODO: Integerのエンコード処理を実装
        raise NotImplementedError("encode_integer() is not implemented yet")

    def encode_bulk_string(self, value: str | None) -> bytes:
        """Bulk Stringをエンコード.

        Args:
            value: エンコードする文字列（Noneの場合はNull Bulk String）

        Returns:
            RESP Bulk String形式（例: $3\\r\\nfoo\\r\\n または $-1\\r\\n）

        実装のヒント:
        - Noneの場合: "$-1\\r\\n"
        - 文字列の場合: "$length\\r\\n" + データ + "\\r\\n"
        """
        # TODO: Bulk Stringのエンコード処理を実装
        raise NotImplementedError("encode_bulk_string() is not implemented yet")


class RESPProtocolError(Exception):
    """RESPプロトコルのパースエラー."""

    pass
