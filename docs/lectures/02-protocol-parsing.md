# RESPプロトコルのパースとエンコード

## 学習目標

このセクションでは、RESPの全データ型の詳細仕様、RESPメッセージをパースするアルゴリズム、Pythonでのエンコード実装パターン、よくある落とし穴とその回避方法、そしてバイナリセーフな通信の実現方法について学びます。

所要時間: 約15分（理論5分＋実装10分）

## 前提知識

バイト列とUTF-8エンコーディングの基礎、Pythonの文字列操作、そしてStreamReader/StreamWriterの使い方（前セクション）を理解していることを前提としています。

## RESP

RESP（Redis serialization protocol）は、Redis serverとRedis clientsが通信するためのプロトコルです。実装や解析が容易で、人間が読みやすいという特徴があります。

クライアントはRedisサーバーにコマンドを `Bulk String` の `Array` として送信します。`Array` の最初の（場合によっては2番目の）`Bulk String`はコマンド名です。`Array`のそれ以降の要素はコマンドの引数です。
サーバーはRESP型で応答します。応答の型はコマンドの実装と、場合によってはクライアントのプロトコルバージョンによって決まります。

`Bulk String`, `Array`, 「応答の型」など、データ型に関する言及が突然出てきて戸惑われたかもしれません。まずは、RedisがサポートするRESPデータ型を一つずつ確認しましょう。

## RESPデータ型の詳細

RESPには5つの基本データ型があります。各データ型は、先頭1バイトで識別されます。

### 1. Simple Strings（単純な文字列）

形式: `+{文字列}\r\n`

!!! warning
    Simple Stringsでは、改行文字（\\rや\\n）を含めてはいけません。必要な場合はBulk Stringsを使用してください。

用途: 短い成功メッセージ（OK、PONGなど）

例:

```
+OK\r\n
+PONG\r\n
```


Pythonでの表現:

```python
# バイト列
b'+OK\r\n'

# パース結果
"OK"
```

### 2. Errors（エラー）

形式: `-{エラーメッセージ}\r\n`

用途: エラー通知

例:

```
-ERR unknown command 'asdf'\r\n
-WRONGTYPE Operation against a key holding the wrong kind of value\r\n
```

ErrorsはSimple Stringsと同じ形式ですが、先頭が`-`になっており、クライアントはこれをエラーとして扱います。'-'の直後の最初の大文字の単語（`ERR` や `WRONGTYPE`など）は、返却されるエラーの種類を表しており、error prefixと呼ばれます。

Pythonでの表現:

```python
# バイト列
b'-ERR unknown command \'asdf\'\r\n'

# パース結果（エラーとして扱う）
raise CommandError("ERR unknown command 'asdf'")
```

### 3. Integers（整数）

形式: `:{整数}\r\n`

!!! note
    `:` の直後は `+` または `-` を取ることができます。どちらもなければ `+` として扱われます。

用途: 数値の応答（INCR、TTL、EXPIREなど）としての使用。コマンドの種別に応じて意味が異なる。

例:

```
:0\r\n        # 0
:42\r\n       # 42
:-1\r\n       # -1（TTLでキーが存在しない場合）
:1000\r\n     # 1000
```

**Pythonでの表現**:

```python
# バイト列
b':42\r\n'

# パース結果
42  # int型
```

### 4. Bulk Strings（長さ指定付き文字列）

形式: `${長さ}\r\n{データ}\r\n`

用途: 任意の文字列データ、バイナリデータ

!!! info
    「任意の文字列」とはいえ、 文字列のサイズは`proto-max-bulk-len` の設定値に制限されます。デフォルトでは512MBです。

例:

```
$5\r\n         ← データの長さ（5バイト）
hello\r\n      ← データ

$11\r\n        ← データの長さ（11バイト）
Hello\nWorld\r\n  ← 改行を含むデータ
```

Null値:

```
$-1\r\n        ← 長さ-1はNullを示す
```

空文字列:

```
$0\r\n         ← 長さ0
\r\n           ← 空データ
```

Bulk Stringsは長さを事前に指定することで、改行文字やNull文字を含むデータも安全に扱え、Null値の表現も可能です。

Pythonでの表現:

```python
# 通常の文字列
b'$5\r\nhello\r\n'  # → "hello"

# Null
b'$-1\r\n'  # → None

# 空文字列
b'$0\r\n\r\n'  # → ""
```

### 5. Arrays（配列）

形式: `*{要素数}\r\n{要素1}{要素2}...`

用途: コマンドの送信、複数値の応答（LRANGEコマンドなど）

例1: `PING`コマンド

```
*1\r\n         ← 要素数1
$4\r\n         ← 1番目の要素の長さ
PING\r\n       ← データ
```

**例2**: `GET mykey`コマンド

```
*2\r\n         ← 要素数2
$3\r\n         ← 1番目の要素の長さ
GET\r\n        ← データ
$5\r\n         ← 2番目の要素の長さ
mykey\r\n      ← データ
```

**例3**: `SET key value`コマンド

```
*3\r\n         ← 要素数3
$3\r\n
SET\r\n
$3\r\n
key\r\n
$5\r\n
value\r\n
```

空配列:

```
*0\r\n         ← 要素数0
```

Null配列:

```
*-1\r\n        ← Null
```

Pythonでの表現:

```python
# GET mykey
b'*2\r\n$3\r\nGET\r\n$5\r\nmykey\r\n'  # → ["GET", "mykey"]

# 空配列
b'*0\r\n'  # → []

# Null
b'*-1\r\n'  # → None
```

## RESPのパース

### コマンドパースの手順

`GET mykey`コマンドをパースする手順を詳しく見ていきます。

**入力データ**:

```
*2\r\n$3\r\nGET\r\n$5\r\nmykey\r\n
```

**ステップ1**: 最初の行を読む

```python
line = await reader.readuntil(b'\r\n')  # b'*2\r\n'
line = line[:-2]  # CRLF削除 → b'*2'
```

**ステップ2**: 先頭文字で型を判定

```python
if line[0:1] == b'*':
    # 配列型
    count = int(line[1:])  # 2
```

**ステップ3**: 各要素をループで読む

```python
result = []
for i in range(count):  # 2回繰り返す
    # 各要素を読む
    element = await parse_bulk_string(reader)
    result.append(element)
```

**ステップ4**: Bulk Stringをパース（1番目: "GET"）

```python
# $3\r\n を読む
length_line = await reader.readuntil(b'\r\n')  # b'$3\r\n'
length_line = length_line[:-2]  # → b'$3'
length = int(length_line[1:])  # → 3

# データ + \r\n を読む（3バイト + 2バイト = 5バイト）
data = await reader.readexactly(length + 2)  # b'GET\r\n'
data = data[:-2]  # CRLF削除 → b'GET'

# UTF-8でデコード
element = data.decode('utf-8')  # "GET"
```

**ステップ5**: Bulk Stringをパース（2番目: "mykey"）

```python
# $5\r\n を読む
length_line = await reader.readuntil(b'\r\n')  # b'$5\r\n'
length = int(length_line[1:-2])  # → 5

# データ + \r\n を読む
data = await reader.readexactly(5 + 2)  # b'mykey\r\n'
element = data[:-2].decode('utf-8')  # "mykey"
```

**ステップ6**: 結果を返す

```python
result = ["GET", "mykey"]
```

### パーサ実装例

```python
import asyncio
from asyncio import StreamReader

class RESPProtocolError(Exception):
    """RESPプロトコルエラー"""
    pass

class RESPParser:
    """RESPプロトコルのパーサー"""

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
```

## RESPのエンコード

### エンコードのパターン

サーバからクライアントへの応答をエンコードする処理を実装します。

#### 1. Simple Stringのエンコード

```python
def encode_simple_string(value: str) -> bytes:
    """Simple Stringをエンコードする"""
    return f"+{value}\r\n".encode('utf-8')

# 例
encode_simple_string("OK")      # → b'+OK\r\n'
encode_simple_string("PONG")    # → b'+PONG\r\n'
```

#### 2. Errorのエンコード

```python
def encode_error(message: str) -> bytes:
    """エラーメッセージをエンコードする"""
    return f"-{message}\r\n".encode('utf-8')

# 例
encode_error("ERR unknown command")
# → b'-ERR unknown command\r\n'
```

#### 3. Integerのエンコード

```python
def encode_integer(value: int) -> bytes:
    """整数をエンコードする"""
    return f":{value}\r\n".encode('utf-8')

# 例
encode_integer(42)     # → b':42\r\n'
encode_integer(-1)     # → b':-1\r\n'
encode_integer(0)      # → b':0\r\n'
```

#### 4. Bulk Stringのエンコード

```python
def encode_bulk_string(value: str | None) -> bytes:
    """Bulk Stringをエンコードする"""
    if value is None:
        # Null値
        return b'$-1\r\n'

    # バイト列に変換
    data = value.encode('utf-8')
    length = len(data)  # バイト長を取得

    # $<length>\r\n<data>\r\n
    return f"${length}\r\n".encode('utf-8') + data + b'\r\n'

# 例
encode_bulk_string("hello")
# → b'$5\r\nhello\r\n'

encode_bulk_string(None)
# → b'$-1\r\n'

encode_bulk_string("")
# → b'$0\r\n\r\n'

encode_bulk_string("こんにちは")  # 日本語（15バイト）
# → b'$15\r\n\xe3\x81\x93\xe3\x82\x93\xe3\x81\xab\xe3\x81\xa1\xe3\x81\xaf\r\n'
```

#### 5. Redisサーバーからのレスポンスのエンコード

複数の型を自動判別してエンコードする

```python
def encode_response(value: str | int | None) -> bytes:
    """応答を適切な形式でエンコードする"""
    if value is None:
        # Null Bulk String
        return encode_bulk_string(None)
    elif isinstance(value, int):
        # Integer
        return encode_integer(value)
    elif isinstance(value, str):
        # Bulk String
        return encode_bulk_string(value)
    else:
        raise ValueError(f"Unsupported type: {type(value)}")

# 例
encode_response("hello")   # → b'$5\r\nhello\r\n'
encode_response(42)        # → b':42\r\n'
encode_response(None)      # → b'$-1\r\n'
```

## よくある落とし穴と回避方法

以下の点に注意してRESPプロトコルの実装を行う必要があります：

1. **CRLF削除忘れ**: `readuntil(b'\r\n')`で読んだ行には末尾に`\r\n`が含まれているため、`line[:-2]`で削除してから処理する必要があります。削除しないと`int()`変換などでエラーが発生します。

2. **バイト長と文字数の混同**: Bulk Stringの長さは文字数ではなくバイト数で指定します。特にマルチバイト文字（日本語など）を扱う場合、`len(text)`ではなく`len(text.encode('utf-8'))`を使用する必要があります。

3. **readexactly()の使い忘れ**: 指定バイト数のデータを読む際は、`read()`ではなく`readexactly()`を使用します。`read()`は指定バイト数未満のデータを返す可能性がありますが、`readexactly()`は正確に指定バイト数が揃うまで待機し、データが不足する場合は`IncompleteReadError`を発生させます。

4. **UTF-8デコードエラー**: バイト列を文字列にデコードする際は、不正なUTF-8データによる`UnicodeDecodeError`に備えて、try-except文でエラーハンドリングを行う必要があります。

5. **Null値の処理忘れ**: Bulk Stringの長さが`-1`の場合はNull値を表します。データ読み取り前に長さをチェックし、`-1`の場合は特別に処理する必要があります。そうしないと`readexactly()`に負の値が渡されてエラーになります。

## 実装ガイド（ハンズオン）

ここまで学んだ内容を活かして、RESPプロトコルのパース・エンコードを実装しましょう！（目安時間: 15分）

### 実装する内容

1. `mini_redis/protocol.py` を開く
2. `parse_command()` メソッドを実装
   - `reader.readuntil(b'\r\n')` で1行ずつ読み取る
   - Arrays形式 (`*N\r\n`) をパース
   - Bulk Strings形式 (`$length\r\ndata\r\n`) をパース
3. エンコード関数を実装
   - `encode_simple_string()`: `+OK\r\n`
   - `encode_integer()`: `:42\r\n`
   - `encode_bulk_string()`: `$3\r\nfoo\r\n` または `$-1\r\n`
   - `encode_error()`: `-ERR message\r\n`

### 実装のポイント

#### パース時の注意点

1. **CRLF削除**: `readuntil(b'\r\n')`で読んだ行には末尾に`\r\n`が含まれているので、`line[:-2]`で削除する
2. **Null値の処理**: Bulk Stringの長さが`-1`の場合はNullを表す
3. **バイト長の正確な読み取り**: `readexactly(length + 2)`で指定バイト数＋CRLF分を読む

#### エンコード時の注意点

1. **バイト長と文字数の違い**: `len(text.encode('utf-8'))`でバイト数を取得（文字数ではない）
2. **Null値の表現**: `$-1\r\n`で表す

### よくある間違いと対処法

#### 1. CRLF削除忘れ

```python
# ❌ 間違い
line = await reader.readuntil(b"\r\n")
# \r\nが含まれたまま

# ✅ 正しい
line = await reader.readuntil(b"\r\n")
line = line[:-2]  # \r\nを削除
```

#### 2. Bulk Stringの長さ計算ミス

```python
# ❌ 間違い
length = len(value)  # 文字数

# ✅ 正しい
value_bytes = value.encode('utf-8')
length = len(value_bytes)  # バイト数
```

#### 3. readexactly()の使い忘れ

```python
# ❌ 間違い
data = await reader.read(length)  # 指定バイト数未満の可能性

# ✅ 正しい
data = await reader.readexactly(length + 2)  # データ + \r\n
```

### テストで確認

```bash
# プロトコルのテストのみ実行
pytest tests/test_protocol.py -v

# 特定のテストクラスのみ
pytest tests/test_protocol.py::TestRESPParser -v
```

### デバッグのヒント

バイト列を確認するときは、`repr()`を使う：

```python
print(f"Received: {line!r}")
# 出力例: Received: b'*2\r\n'
```

もし詰まった場合は：

1. `WORKSHOP_GUIDE.md`の「よくある間違い」セクションを確認
2. テストコードで期待される動作を確認
3. 完成版コード（`solutions/mini_redis/protocol.py`）と比較

## 次のステップ

RESPプロトコルのパース・エンコードを学び、実装しました。次は、これらを使ってRedisコマンドを実装します。

👉 次のセクション: [03-commands.md](03-commands.md)
