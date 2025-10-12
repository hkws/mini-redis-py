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
        # 1. 最初の行を読み取る（配列の要素数）
        line = await reader.readuntil(b"\r\n")
        line = line[:-2]  # \r\nを削除

        # 配列のプレフィックス'*'を確認
        if not line.startswith(b"*"):
            raise RESPProtocolError(f"Expected array prefix '*', got: {line!r}")

        # 配列の要素数を取得
        try:
            array_length = int(line[1:])
        except ValueError as e:
            raise RESPProtocolError(f"Invalid array length: {line!r}") from e

        # 2. 各要素をBulk String形式で読み取る
        result: list[str] = []
        for _ in range(array_length):
            # Bulk Stringの長さを読み取る
            length_line = await reader.readuntil(b"\r\n")
            length_line = length_line[:-2]  # \r\nを削除

            # Bulk Stringのプレフィックス'$'を確認
            if not length_line.startswith(b"$"):
                raise RESPProtocolError(
                    f"Expected bulk string prefix '$', got: {length_line!r}"
                )

            # Bulk Stringの長さを取得
            try:
                bulk_length = int(length_line[1:])
            except ValueError as e:
                raise RESPProtocolError(f"Invalid bulk string length: {length_line!r}") from e

            # 指定された長さ分のデータを読み取る
            data = await reader.readexactly(bulk_length)

            # 終端の\r\nを読み取って検証
            terminator = await reader.readexactly(2)
            if terminator != b"\r\n":
                raise RESPProtocolError(f"Expected \\r\\n terminator, got: {terminator!r}")

            # UTF-8デコード
            result.append(data.decode("utf-8"))

        return result

    def encode_simple_string(self, value: str) -> bytes:
        """Simple Stringをエンコード.

        Args:
            value: エンコードする文字列

        Returns:
            RESP Simple String形式（例: +OK\\r\\n）

        実装のヒント:
        プレフィックス '+' + 文字列 + '\\r\\n'
        """
        return f"+{value}\r\n".encode()

    def encode_error(self, message: str) -> bytes:
        """Errorをエンコード.

        Args:
            message: エラーメッセージ

        Returns:
            RESP Error形式（例: -ERR message\\r\\n）

        実装のヒント:
        プレフィックス '-' + メッセージ + '\\r\\n'
        """
        return f"-{message}\r\n".encode()

    def encode_integer(self, value: int) -> bytes:
        """Integerをエンコード.

        Args:
            value: エンコードする整数

        Returns:
            RESP Integer形式（例: :42\\r\\n）

        実装のヒント:
        プレフィックス ':' + 整数の文字列表現 + '\\r\\n'
        """
        return f":{value}\r\n".encode()

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
        if value is None:
            return b"$-1\r\n"

        # UTF-8エンコード後のバイト長を計算
        value_bytes = value.encode()
        length = len(value_bytes)
        return f"${length}\r\n".encode() + value_bytes + b"\r\n"


class RESPProtocolError(Exception):
    """RESPプロトコルのパースエラー."""

    pass
