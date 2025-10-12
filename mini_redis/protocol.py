"""RESP (REdis Serialization Protocol) parser and encoder.

このモジュールは、RESPプロトコルのパース（バイト列→Pythonオブジェクト）と
エンコード（Pythonオブジェクト→バイト列）を担当します。

【実装順序のガイド】
1. encode_simple_string() - 最もシンプルなエンコード
2. encode_error() - encode_simple_string()と同じパターン
3. encode_integer() - 整数のエンコード
4. encode_bulk_string() - Null Bulk Stringの処理に注意
5. parse_command() - 複雑だが、ステップバイステップで実装
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

        【実装ステップ】
        ステップ1: 配列の要素数を読み取る
        ─────────────────────────────────
        1. reader.readuntil(b'\\r\\n')で1行を読み取る
        2. 末尾の\\r\\nを削除: line = line[:-2]
        3. 最初の文字が'*'であることを確認（Arraysのプレフィックス）
        4. 残りの部分を整数に変換して要素数を取得

        例: b'*2\\r\\n' → 2 (配列には2つの要素)

        ステップ2: 各要素をBulk String形式で読み取る
        ────────────────────────────────────────
        要素数分ループして、以下を繰り返す:
        1. Bulk Stringの長さを読み取る（'$N\\r\\n'）
           - reader.readuntil(b'\\r\\n')で1行読み取り
           - 末尾の\\r\\nを削除
           - '$'を確認し、残りを整数に変換
        2. 指定された長さ分のデータを読み取る
           - reader.readexactly(length)で正確にlengthバイト読み取り
        3. 終端の\\r\\nを読み取って検証
           - reader.readexactly(2)で2バイト読み取り
           - b'\\r\\n'であることを確認
        4. データをUTF-8でデコードしてリストに追加

        例: b'$3\\r\\nGET\\r\\n' → "GET"

        【よくある間違い】
        ❌ readuntil()で読み取った後、\\r\\nを削除し忘れる
        ❌ Bulk Stringのデータ長を「文字数」ではなく「バイト数」で読み取る必要がある
        ❌ 終端の\\r\\nを読み取り忘れる

        【デバッグのヒント】
        - バイト列を確認: print(f"Received: {line!r}")
        - 各ステップでprintデバッグを入れて、どこまで進んでいるか確認
        """
        # TODO: ステップ1を実装してください
        # 1-1. reader.readuntil(b'\r\n')で最初の行を読み取る
        # 1-2. 末尾の\r\nを削除
        # 1-3. 最初の文字が'*'であることを確認（でなければRESPProtocolErrorをraise）
        # 1-4. 残りの部分をint()で整数に変換して配列の要素数を取得
        #      （変換エラーの場合はRESPProtocolErrorをraise）

        # TODO: ステップ2を実装してください
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

        【実装ステップ】
        1. プレフィックス '+' を先頭に追加
        2. 文字列を追加
        3. 終端 '\\r\\n' を追加
        4. .encode()でバイト列に変換

        例: "PONG" → b'+PONG\\r\\n'

        【ヒント】
        f-stringを使うと簡単: f"+{value}\\r\\n".encode()
        """
        # TODO: 実装してください
        raise NotImplementedError("encode_simple_string()を実装してください")

    def encode_error(self, message: str) -> bytes:
        """Errorをエンコード.

        Args:
            message: エラーメッセージ

        Returns:
            RESP Error形式（例: -ERR message\\r\\n）

        【実装ステップ】
        1. プレフィックス '-' を先頭に追加
        2. エラーメッセージを追加
        3. 終端 '\\r\\n' を追加
        4. .encode()でバイト列に変換

        例: "ERR unknown command" → b'-ERR unknown command\\r\\n'

        【ヒント】
        encode_simple_string()とほぼ同じパターン（プレフィックスが'-'）
        """
        # TODO: 実装してください
        raise NotImplementedError("encode_error()を実装してください")

    def encode_integer(self, value: int) -> bytes:
        """Integerをエンコード.

        Args:
            value: エンコードする整数

        Returns:
            RESP Integer形式（例: :42\\r\\n）

        【実装ステップ】
        1. プレフィックス ':' を先頭に追加
        2. 整数を文字列に変換して追加
        3. 終端 '\\r\\n' を追加
        4. .encode()でバイト列に変換

        例: 42 → b':42\\r\\n'

        【ヒント】
        f-stringを使うと簡単: f":{value}\\r\\n".encode()
        """
        # TODO: 実装してください
        raise NotImplementedError("encode_integer()を実装してください")

    def encode_bulk_string(self, value: str | None) -> bytes:
        """Bulk Stringをエンコード.

        Args:
            value: エンコードする文字列（Noneの場合はNull Bulk String）

        Returns:
            RESP Bulk String形式（例: $3\\r\\nfoo\\r\\n または $-1\\r\\n）

        【実装ステップ】
        ステップ1: Noneの場合の処理
        ─────────────────────────
        value が None の場合、Null Bulk String "$-1\\r\\n" を返す

        ステップ2: 文字列の場合の処理
        ───────────────────────────
        1. value.encode()でUTF-8バイト列に変換
        2. len(value_bytes)でバイト数を取得
        3. "$length\\r\\n"を作成してエンコード
        4. データ本体（value_bytes）を追加
        5. 終端 "\\r\\n" を追加

        例:
        - None → b'$-1\\r\\n'
        - "foo" → b'$3\\r\\nfoo\\r\\n'
        - "こんにちは" → b'$15\\r\\n\\xe3\\x81\\x93\\xe3\\x82\\x93\\xe3\\x81\\xab\\xe3\\x81\\xa1\\xe3\\x81\\xaf\\r\\n'

        【よくある間違い】
        ❌ len(value)（文字数）を使う → 正しくはlen(value.encode())（バイト数）
        ❌ Noneの処理を忘れる

        【ヒント】
        1. まずNoneの場合を処理: if value is None: return b"$-1\\r\\n"
        2. 文字列の場合: f"${length}\\r\\n".encode() + value_bytes + b"\\r\\n"
        """
        # TODO: ステップ1を実装してください
        # value が None の場合、b"$-1\r\n" を返す

        # TODO: ステップ2を実装してください
        # 2-1. value.encode()でUTF-8バイト列に変換
        # 2-2. len(value_bytes)でバイト数を取得
        # 2-3. f"${length}\r\n".encode() + value_bytes + b"\r\n" を返す

        raise NotImplementedError("encode_bulk_string()を実装してください")


class RESPProtocolError(Exception):
    """RESPプロトコルのパースエラー.

    【使い方】
    不正なRESP形式を検出したときにraiseします。

    例:
        raise RESPProtocolError(f"Expected array prefix '*', got: {line!r}")
    """

    pass
