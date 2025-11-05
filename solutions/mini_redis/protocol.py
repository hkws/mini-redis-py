"""RESP (REdis Serialization Protocol) parser and encoder.

このモジュールは、RESPプロトコルのパース（バイト列→Pythonオブジェクト）と
エンコード（Pythonオブジェクト→バイト列）を担当します。

"""

from asyncio import StreamReader
from dataclasses import dataclass
from typing import Optional


@dataclass
class SimpleString:
    """Simple String型を表すラッパー (+)"""
    value: str

@dataclass
class RedisError:
    """Error型を表すラッパー (-)"""
    value: str

@dataclass
class Integer:
    """Integer型を表すラッパー (:)"""
    value: int

@dataclass
class BulkString:
    """Bulk String型を表すラッパー ($)"""
    value: str | None

@dataclass
class Array:
    """Array型を表すラッパー (*)"""
    items: list | None  # Noneの場合はNull Array

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
        """コマンド（配列）をパースする"""
        # 最初の行を読む: *N\r\n
        line = await reader.readuntil(b'\r\n')
        line = line[:-2]  # CRLF削除

        # 配列かチェック
        if not line.startswith(b'*'):
            raise RESPProtocolError("Expected array")

        # 要素数を取得
        try:
            count = int(line[1:])
        except ValueError:
            raise RESPProtocolError("Invalid array length")

        # 各要素を読む
        result = []
        for _ in range(count):
            element = await self._parse_bulk_string(reader)
            result.append(element)

        return result

    async def _parse_bulk_string(self, reader: StreamReader) -> str:
        """Bulk Stringをパースする"""
        # 長さ行を読む: $N\r\n
        length_line = await reader.readuntil(b'\r\n')
        length_line = length_line[:-2]  # CRLF削除

        # Bulk Stringかチェック
        if not length_line.startswith(b'$'):
            raise RESPProtocolError("Expected bulk string")

        # 長さを取得
        try:
            length = int(length_line[1:])
        except ValueError:
            raise RESPProtocolError("Invalid bulk string length")

        # Null値のチェック
        if length == -1:
            raise RESPProtocolError("Unexpected null value")

        # データを読む（データ + \r\n）
        data = await reader.readexactly(length + 2)

        # 末尾が\r\nかチェック
        if data[-2:] != b'\r\n':
            raise RESPProtocolError("Expected CRLF after bulk string")

        # CRLF削除してUTF-8デコード
        return data[:-2].decode('utf-8')

    def encode_simple_string(self, value: str) -> bytes:
        """Simple Stringをエンコードする"""
        return f"+{value}\r\n".encode('utf-8')

    def encode_error(self, message: str) -> bytes:
        """エラーメッセージをエンコードする"""
        return f"-{message}\r\n".encode('utf-8')

    def encode_integer(self, value: int) -> bytes:
        """整数をエンコードする"""
        return f":{value}\r\n".encode('utf-8')

    def encode_bulk_string(self, value: str | None) -> bytes:
        """Bulk Stringをエンコードする"""
        if value is None:
            # Null値
            return b'$-1\r\n'

        # バイト列に変換
        data = value.encode('utf-8')
        length = len(data)  # バイト長を取得

        # $<length>\r\n<data>\r\n
        return f"${length}\r\n".encode('utf-8') + data + b'\r\n'

    def encode_array(self, items: list | None) -> bytes:
        """Arrayをエンコード"""
        if items is None:
            # Null Array
            return b'*-1\r\n'

        # 要素数
        result = f"*{len(items)}\r\n".encode('utf-8')

        # 各要素をエンコード
        for item in items:
            result += self.encode_response(item)

        return result

    def encode_response(self, result) -> bytes:
        """応答を適切な形式でエンコードする"""
        if isinstance(result, SimpleString):
            return self.encode_simple_string(result.value)
        elif isinstance(result, RedisError):
            return self.encode_error(result.value)
        elif isinstance(result, Integer):
            return self.encode_integer(result.value)
        elif isinstance(result, BulkString):
            return self.encode_bulk_string(result.value)
        elif isinstance(result, Array):
            return self.encode_array(result.items)
        else:
            raise ValueError(f"Unsupported type: {type(result)}")


class RESPProtocolError(Exception):
    """RESPプロトコルのパースエラー.

    例:
        raise RESPProtocolError(f"Expected array prefix '*', got: {line!r}")
    """

    pass
