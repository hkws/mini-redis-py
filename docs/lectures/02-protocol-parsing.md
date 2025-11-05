# RESPプロトコルのパースとエンコード

## 学習目標

このセクションでは、RESPの全データ型の詳細仕様、RESPメッセージをパースするアルゴリズム、Pythonでのエンコード実装パターン、よくある落とし穴とその回避方法、そしてバイナリセーフな通信の実現方法について学びます。

所要時間: 約15分（理論5分＋実装10分）

## 前提知識

Pythonの文字列操作、そしてStreamReader/StreamWriterの使い方（前セクション）を理解していることを前提としています。

## RESP

RESP（Redis serialization protocol）は、Redis serverとRedis clientsが通信するためのプロトコルです。実装や解析が容易で、人間が読みやすいという特徴があります。

クライアントはRedisサーバーにコマンドを `Bulk String` の `Array` として送信します。`Array` の最初の（場合によっては2番目の）`Bulk String`はコマンド名です。`Array`のそれ以降の要素はコマンドの引数です。
サーバーはRESPデータ型で応答します。応答の型はコマンドの実装と、場合によってはクライアントのプロトコルバージョンによって決まります。

`Bulk String`, `Array`, RESPデータ型など、データ型に関する言及が突然出てきて戸惑われたかもしれません。まずは、RedisがサポートするRESPデータ型を一つずつ確認しましょう。

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

ErrorsはSimple Stringsと同じ形式ですが、先頭が`-`になっており、クライアントはこれをエラーとして扱います。'-'の直後の最初の大文字の単語（`ERR` や `WRONGTYPE`など）は、返却されるエラーの種類を表しており、Error Prefixと呼ばれます。

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

用途: 数値の応答（INCR、TTL、EXPIREなど）としての使用。その際の応答の意味はコマンドの種別による。

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

!!! note パースとエンコードでの型の扱い
    **パース時**（クライアントからのメッセージの受信時）は、上記のようにPythonの基本型（`str`、`int`、`list`、`None`）で表現できます。

    **エンコード時**（クライアントへのメッセージ送信時）は、Simple StringとBulk String、ErrorとSimple Stringなどを区別する必要があります。これは、Pythonの基本型だけでは区別できないため、後述するように型ラッパークラスを使用します。

    詳しくは「[5. Redisサーバーからのレスポンスのエンコード](#5-redisサーバーからのレスポンスのエンコード)」を参照してください。


## RESPのパース実装

### コマンドパースの手順

`GET mykey`コマンドをパースする手順を詳しく見ていきます。前述の通り、コマンドは `Bulk Strings` の `Array` として送信されます。よって、`GET mykey`は以下のように表現されます。

```
*2\r\n$3\r\nGET\r\n$5\r\nmykey\r\n
```

これを入力とした場合の、パース手順は以下の通りです。

**ステップ1**: 最初の行（\r\nまで）を読む

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

## RESPのエンコード実装

### エンコードのパターン

サーバからクライアントへの応答をエンコードする処理を実装します。

#### 1. Simple Stringのエンコード

```python
def encode_simple_string(self, value: str) -> bytes:
    """Simple Stringをエンコードする"""
    return f"+{value}\r\n".encode('utf-8')

# 例
encode_simple_string("OK")      # → b'+OK\r\n'
encode_simple_string("PONG")    # → b'+PONG\r\n'
```

#### 2. Errorのエンコード

```python
def encode_error(self, message: str) -> bytes:
    """エラーメッセージをエンコードする"""
    return f"-{message}\r\n".encode('utf-8')

# 例
encode_error("ERR unknown command")
# → b'-ERR unknown command\r\n'
```

#### 3. Integerのエンコード

```python
def encode_integer(self, value: int) -> bytes:
    """整数をエンコードする"""
    return f":{value}\r\n".encode('utf-8')

# 例
encode_integer(42)     # → b':42\r\n'
encode_integer(-1)     # → b':-1\r\n'
encode_integer(0)      # → b':0\r\n'
```

#### 4. Bulk Stringのエンコード

```python
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

#### 5. Arrayのエンコード

```python
def encode_array(self, items: list | None) -> bytes:
    """Arrayをエンコード"""
    if items is None:
        # Null Array
        return b'*-1\r\n'

    # 要素数
    result = f"*{len(items)}\r\n".encode('utf-8')

    # 各要素をエンコード
    for item in items:
        result += self.encode_response(item) # 後述

    return result
```

#### 5. Redisサーバーからのレスポンスのエンコード

前述の通り、str, intのようなPythonの基本型だけでは、RESPデータ型を区別できません。例えば、Simple Stringの"OK"とBulk Stringの"OK"は同じPythonの`str`型ですが、RESPでは異なる型です。

そこで、RESPの5つのデータ型すべてに対応する型ラッパーを定義します。コマンド実装では、これらの型ラッパーを使って応答を返すようにし、、エンコード関数では型ラッパーに基づいて適切なエンコード関数を呼び出します。

以下は、型ラッパーおよびエンコード関数の実装例です。

```python
from dataclasses import dataclass

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

# 例
encode_response(SimpleString("OK"))              # → b'+OK\r\n'
encode_response(RedisError("ERR unknown"))       # → b'-ERR unknown\r\n'
encode_response(Integer(42))                     # → b':42\r\n'
encode_response(BulkString("hello"))             # → b'$5\r\nhello\r\n'
encode_response(BulkString(None))                # → b'$-1\r\n'
encode_response(Array([
    BulkString("foo"),
    BulkString("bar")
]))                                              # → b'*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n'
encode_response(Array(None))                     # → b'*-1\r\n'
```

**使用例（コマンド実装）**:

```python
# PINGコマンド → Simple Stringで応答
return SimpleString("PONG")

# GETコマンド → Bulk Stringで応答
value = storage.get(key)
return BulkString(value)  # valueがNoneでもOK

# INCRコマンド → Integerで応答
new_value = storage.incr(key)
return Integer(new_value)

# （本ワークショップでは実装対象外）LRANGEコマンド → Arrayで応答
values = storage.lrange(key, start, stop)
return Array([BulkString(v) for v in values])

# エラー応答
return RedisError("ERR unknown command")
```

**型の使い分け**:

| RESP型 | ラッパークラス | 使用場面 |
|--------|--------------|----------|
| Simple String | `SimpleString` | 短い成功メッセージ（OK、PONGなど） |
| Error | `RedisError` | エラー応答 |
| Integer | `Integer` | 数値応答（INCR、TTL、EXPIREなど） |
| Bulk String | `BulkString` | 文字列データ（GET、バイナリデータ） |
| Array | `Array` | 複数値の応答（KEYS、LRANGEなど） |


## 実装ガイド（ハンズオン）

ここまで学んだ内容を活かして、RESPプロトコルのパース・エンコードを実装しましょう！（目安時間: 15分）

### 実装する内容

1. `mini_redis/protocol.py` を開く
2. `parse_command()` メソッドを実装
   - `reader.readuntil(b'\r\n')` で1行ずつ読み取る
   - Arrays形式 (`*N\r\n`) をパース
   - Bulk Strings形式 (`$length\r\ndata\r\n`) をパース
3. エンコード関数を実装
   - 型ラッパーを定義
   - `encode_simple_string()`: `+OK\r\n`
   - `encode_integer()`: `:42\r\n`
   - `encode_bulk_string()`: `$3\r\nfoo\r\n` または `$-1\r\n`
   - `encode_error()`: `-ERR message\r\n`
   - `encode_array()`: `*N\r\n{要素1}{要素2}...`
   - `encode_response()`: 型ラッパーに基づいて適切なエンコード関数を呼び出す

### 実装のポイント

#### パース時の注意点

1. **CRLF削除**: `readuntil(b'\r\n')`で読んだ行には末尾に`\r\n`が含まれているので、`line[:-2]`で削除する
2. **Null値の処理**: Bulk Stringの長さが`-1`の場合はNullを表す
3. **バイト長の正確な読み取り**: `readexactly(length + 2)`で指定バイト数＋CRLF分を読む

#### エンコード時の注意点

1. **バイト長と文字数の違い**: `len(text.encode('utf-8'))`でバイト数を取得（文字数ではない）
2. **Null値の表現**: `$-1\r\n`で表す

### テストで確認

```bash
# すべてのテストを実行
pytest tests/step02_protocol/ -v

# 特定のテストクラスのみ
pytest tests/step02_protocol/test_resp_protocol.py::TestStep02RESPParser -v
pytest tests/step02_protocol/test_resp_protocol.py::TestStep02RESPEncoder -v
```

## 次のステップ

RESPプロトコルのパース・エンコードを学び、実装しました。次は、これらを使ってRedisコマンドを実装します。

👉 次のセクション: [03-commands.md](03-commands.md)
