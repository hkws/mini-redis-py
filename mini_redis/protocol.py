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
        """
        # TODO: parse_command()を実装してください
        # 1-1. reader.readuntil(b'\r\n')で最初の行を読み取る
        # 1-2. 末尾の\r\nを削除
        # 1-3. 最初の文字が'*'であることを確認（でなければRESPProtocolErrorをraise）
        # 1-4. 残りの部分をint()で整数に変換して配列の要素数を取得
        #      （変換エラーの場合はRESPProtocolErrorをraise）

        # TODO: Bulk Stringのパースを実装してください
        # 2-1. 空のリストを作成: result = []
        # 2-2. 配列の要素数分ループ
        #   2-2-1. Bulk Stringの長さを読み取る
        #   2-2-2. 指定された長さ分のデータを読み取る
        #   2-2-3. 終端の\r\nを読み取って検証
        #   2-2-4. データをUTF-8でデコードしてリストに追加
        # 2-3. resultを返す
        raise NotImplementedError("parse_command()を実装してください")

    def encode_simple_string(self, value: str) -> bytes:
        """Simple Stringをエンコード.

        Args:
            value: エンコードする文字列

        Returns:
            RESP Simple String形式（例: +OK\\r\\n）

        例: "PONG" → b'+PONG\\r\\n'

        """
        raise NotImplementedError("encode_simple_string()を実装してください")

    def encode_error(self, message: str) -> bytes:
        """Errorをエンコード.

        Args:
            message: エラーメッセージ

        Returns:
            RESP Error形式（例: -ERR message\\r\\n）
        
        例: "ERR unknown command" → b'-ERR unknown command\\r\\n'

        """
        raise NotImplementedError("encode_error()を実装してください")

    def encode_integer(self, value: int) -> bytes:
        """Integerをエンコード.

        Args:
            value: エンコードする整数

        Returns:
            RESP Integer形式（例: :42\\r\\n）

        例: 42 → b':42\\r\\n'
        
        """
        raise NotImplementedError("encode_integer()を実装してください")

    def encode_bulk_string(self, value: str | None) -> bytes:
        """Bulk Stringをエンコード.

        Args:
            value: エンコードする文字列（Noneの場合はNull Bulk String）

        Returns:
            RESP Bulk String形式（例: $3\\r\\nfoo\\r\\n または $-1\\r\\n）

        """
        # 1. value が None の場合、b"$-1\r\n" を返す

        # 2-1. value.encode()でUTF-8バイト列に変換
        # 2-2. len(value_bytes)でバイト数を取得
        # 2-3. $<length>\r\n<data>\r\n を返す

        raise NotImplementedError("encode_bulk_string()を実装してください")

    def encode_array(self, values: list[str] | None) -> bytes:
        """Arrayをエンコード.

        Args:
            values: エンコードする文字列のリスト（Noneの場合はNull Array）

        Returns:
            RESP Array形式（例: *2\\r\\n$3\\r\\nfoo\\r\\n$3\\r\\nbar\\r\\n または *-1\\r\\n）

        例: ["foo", "bar"] → b'*2\\r\\n$3\\r\\nfoo\\r\\n$3\\r\\nbar\\r\\n'
        例: None → b'*-1\\r\\n'

        """
        raise NotImplementedError("encode_array()を実装してください")

    def encode_response(self, response: str | int | list[str] | None) -> bytes:
        """レスポンスをRESP形式にエンコード.

        Args:
            response: エンコードするレスポンス

        Returns:
            適切なRESP形式のバイト列

        例:
            "OK" → b'+OK\\r\\n'
            42 → b':42\\r\\n'
            "foo" → b'$3\\r\\nfoo\\r\\n'
            ["foo", "bar"] → b'*2\\r\\n$3\\r\\nfoo\\r\\n$3\\r\\nbar\\r\\n'
            None → b'$-1\\r\\n'

        """
        raise NotImplementedError("encode_response()を実装してください")


class RESPProtocolError(Exception):
    """RESPプロトコルのパースエラー.

    例:
        raise RESPProtocolError(f"Expected array prefix '*', got: {line!r}")
    """

    pass
