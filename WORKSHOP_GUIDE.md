# Mini-Redis ワークショップガイド

## はじめに

このワークショップでは、Python/asyncioを使用してRedisの基本機能を実装します。
60〜90分で、RESPプロトコル、asyncio、キー・バリューストア、有効期限管理を学びます。

**📚 学習資料**:
- [アーキテクチャ解説](docs/architecture.md) - システム全体像とレイヤー構造
- [講義資料一覧](docs/lectures/) - 各段階の理論解説

## 学習目標

1. **asyncioによるTCPサーバの実装**: 非同期I/Oの基礎を理解
2. **RESPプロトコルの実装**: Redisの通信フォーマットを学習
3. **基本コマンドの実装**: PING/GET/SET/INCRの動作原理を理解
4. **EXPIRE機能の実装**: Passive + Active期限管理を学習

## セットアップ

```bash
# リポジトリをクローン
git clone <repository-url>
cd mini-redis-py

# 開発用ツールを含めてインストール
pip install -e ".[dev]"

# テストが実行できることを確認（最初は全て失敗するのが正常）
pytest
```

**注意**: 最初はすべてのテストが `NotImplementedError` で失敗します。これは正常です。実装を進めるにつれて、テストが通るようになります。

## プロジェクト構成

詳細なアーキテクチャは [`docs/architecture.md`](docs/architecture.md) を参照してください。

```
mini-redis-py/
├── docs/                # 学習資料
│   ├── architecture.md  # アーキテクチャ解説
│   └── lectures/        # 段階別講義資料
├── mini_redis/          # 学習者向け実装雛形（TODOコメント付き）
│   ├── protocol.py      # RESPプロトコル - 実装が必要
│   ├── storage.py       # データストレージ - 実装が必要
│   ├── commands.py      # コマンド実行 - 実装が必要
│   ├── expiry.py        # 有効期限管理 - 実装が必要
│   └── server.py        # TCPサーバ（一部実装が必要）
├── solutions/           # 完成版コード（参考用）
│   ├── mini_redis/      # 完全に動作する実装
│   └── README.md        # 完成版の使い方
└── tests/               # テストスイート
```

**実装の流れ**: `mini_redis/` ディレクトリのファイルにあるTODOコメントを順番に実装していきます。詰まった場合は、`solutions/` ディレクトリの完成版コードを参考にできます。

## 実装の流れ

### ステップ0: 導入とデモ確認 (5分)

**📚 事前学習**: [Redis基礎とRESP入門（講義資料00）](docs/lectures/00-introduction.md)

**目標**: Redisの基本概念とMini-Redisの完成イメージを理解

1. 完成版のデモを確認する
```bash
# 完成版サーバを起動（別ターミナルで）
python -m solutions.mini_redis

# redis-cliで接続
redis-cli -p 6379

# 基本コマンドを試す
> PING
PONG

> SET mykey "hello"
OK

> GET mykey
"hello"

> INCR counter
(integer) 1

> EXPIRE counter 60
(integer) 1

> TTL counter
(integer) 59
```

2. RESPプロトコルの基本構造を確認
   - Arrays形式: `*2\r\n$4\r\nPING\r\n`
   - Bulk Strings: `$5\r\nhello\r\n`
   - Simple Strings: `+OK\r\n`

**ポイント**: 実装する機能のイメージを掴むことが重要です。講義資料でRedisとRESPの基礎を理解してから実装に進みましょう。

---

### ステップ1: TCPサーバの実装 (15分)

**📚 事前学習**: [asyncio TCPサーバ（講義資料01）](docs/lectures/01-tcp-server.md)

**目標**: asyncioを使ったTCPサーバとクライアント処理ループを実装

1. `mini_redis/server.py` を開く
2. `ClientHandler.handle()` を実装
   - コマンドの読み取り→パース→実行→応答のループ
   - 結果の型判定（str/int/None）とエンコード
   - エラーハンドリング（CommandError、RESPProtocolError等）
   - finally句でクリーンアップ

**重要**: TCPServer.start()とstop()は実装済みです。ClientHandler.handle()のみ実装してください。

**確認方法**:
```bash
pytest tests/test_server.py -v
```

---

### ステップ2: RESPプロトコルの実装 (15分)

**📚 事前学習**: [RESPプロトコル詳細（講義資料02）](docs/lectures/02-protocol-parsing.md)

**目標**: RESPプロトコルのパース・エンコード機能を実装

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

**確認方法**:
```bash
pytest tests/test_protocol.py -v
```

---

### ステップ3: データストレージ層の実装 (15分)

**目標**: インメモリキー・バリューストアを実装

1. `mini_redis/storage.py` を開く
2. 基本操作を実装
   - `get()`: キーの値を取得
   - `set()`: キーに値を設定
   - `delete()`: キーを削除
   - `exists()`: キーの存在確認
3. 有効期限管理を実装
   - `set_expiry()`: 有効期限を設定
   - `get_expiry()`: 有効期限を取得
   - `get_all_keys()`: すべてのキーを取得

**確認方法**:
```bash
pytest tests/test_storage.py -v
```

---

### ステップ4: コマンド実行層の実装 (20分)

**📚 事前学習**: [コマンド実装パターン（講義資料03）](docs/lectures/03-commands.md)

**目標**: Redisコマンドのルーティングと実行を実装

1. `mini_redis/commands.py` を開く
2. `execute()` メソッドを実装
   - コマンド名を取得し、対応するメソッドにルーティング
   - 引数の数と型を検証
3. 各コマンドを実装
   - `execute_ping()`: "PONG"を返す
   - `execute_get()`: キーの値を取得
   - `execute_set()`: キーに値を設定
   - `execute_incr()`: 値を1増加
   - `execute_expire()`: 有効期限を設定
   - `execute_ttl()`: 残り有効秒数を取得

**重要**: GET/INCR/EXPIRE/TTLの最初で `check_and_remove_expired(key)` を呼び出す

**確認方法**:
```bash
pytest tests/test_commands.py -v
```

---

### ステップ5: 有効期限管理の実装 (20分)

**📚 事前学習**: [有効期限管理（講義資料04）](docs/lectures/04-expiry.md)

**目標**: Passive + Active Expiryを実装

1. `mini_redis/expiry.py` を開く
2. `check_and_remove_expired()` を実装 (Passive)
   - 有効期限をチェック
   - 期限切れの場合はキーを削除
3. `start_active_expiry()` を実装 (Active)
   - 1秒ごとにバックグラウンドタスクを実行
   - ランダムに20キーをサンプリング
   - 期限切れキーを削除
   - 削除率が25%を超える場合は即座に再実行

**確認方法**:
```bash
pytest tests/test_expiry.py -v
```

---

### ステップ6: 統合テストと動作確認 (10分)

**📚 振り返り**: [まとめと発展課題（講義資料05）](docs/lectures/05-summary.md)

**目標**: 実装した機能の動作確認と学習内容の振り返り

1. サーバを起動
```bash
python -m mini_redis
```

2. 別のターミナルでredis-cliに接続
```bash
redis-cli -p 6379

# コマンドを試す
> PING
PONG

> SET mykey "hello"
OK

> GET mykey
"hello"

> INCR counter
(integer) 1

> EXPIRE mykey 10
(integer) 1

> TTL mykey
(integer) 9
```

3. 学習内容の振り返り
   - ✅ asyncioを使ったTCPサーバの実装パターン
   - ✅ RESPプロトコルの仕様とパーサの実装
   - ✅ 基本的なRedisコマンドの動作原理
   - ✅ Redisの期限管理メカニズム (Passive + Active Expiration)

**ポイント**: 講義資料05で、習得したスキルと次のステップ（発展課題）を確認しましょう。

## よくある間違いと対処法

### 1. RESPプロトコルのパースエラー

**問題**: `readuntil()` で `\r\n` を読み取った後、削除するのを忘れた

```python
# ❌ 間違い
line = await reader.readuntil(b"\r\n")
# \r\nが含まれたまま

# ✅ 正しい
line = await reader.readuntil(b"\r\n")
line = line[:-2]  # \r\nを削除
```

### 2. Bulk Stringの長さ計算ミス

**問題**: UTF-8エンコード後のバイト長を使わずに文字数を使ってしまった

```python
# ❌ 間違い
length = len(value)  # 文字数

# ✅ 正しい
value_bytes = value.encode('utf-8')
length = len(value_bytes)  # バイト数
```

### 3. Passive Expiryの呼び出し忘れ

**問題**: GETやINCRコマンドで `check_and_remove_expired()` を呼び忘れた

```python
# ❌ 間違い
async def execute_get(self, key: str) -> str | None:
    return self._store.get(key)  # 期限チェックなし

# ✅ 正しい
async def execute_get(self, key: str) -> str | None:
    self._expiry.check_and_remove_expired(key)  # 期限チェック
    return self._store.get(key)
```

### 4. INCRコマンドの型エラー処理

**問題**: 値が整数でない場合のエラー処理を忘れた

```python
# ❌ 間違い
int_value = int(current_value)  # ValueErrorが発生する可能性

# ✅ 正しい
try:
    int_value = int(current_value)
except ValueError as e:
    raise CommandError("ERR value is not an integer or out of range") from e
```

### 5. Active Expiryの削除率チェック

**問題**: 削除率が25%を超えたときの再実行ロジックを実装し忘れた

```python
# ❌ 間違い
# 1回サンプリングして終了

# ✅ 正しい
while True:
    # サンプリングして削除
    expired_count = ...
    if expired_count / sample_size > 0.25:
        continue  # 即座に次のサンプリング
    break  # 削除率が低いので終了
```

## デバッグのヒント

### 1. RESPプロトコルのデバッグ

バイト列を確認するときは、`repr()` を使う：

```python
print(f"Received: {line!r}")
# 出力例: Received: b'*2\r\n'
```

### 2. テストの個別実行

特定のテストだけを実行して素早く確認：

```bash
# 1つのテストクラスだけ実行
pytest tests/test_protocol.py::TestRESPParser -v

# 1つのテストメソッドだけ実行
pytest tests/test_protocol.py::TestRESPParser::test_parse_simple_command -v
```

### 3. asyncioのデバッグ

asyncioのデバッグモードを有効にする：

```python
import asyncio

asyncio.run(main(), debug=True)
```

### 4. ログ出力の追加

デバッグ用にログを追加する：

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug(f"Command: {command}")
```

### 5. 完成版との比較

実装に詰まった場合、完成版のコードを参照できます：

```bash
# 実装と完成版を比較
diff mini_redis/protocol.py solutions/mini_redis/protocol.py

# または、エディタのdiff機能を使用
code --diff mini_redis/protocol.py solutions/mini_redis/protocol.py
```

**推奨アプローチ**:
1. まず`WORKSHOP_GUIDE.md`の「よくある間違い」セクションを確認
2. テストコードで期待される動作を確認
3. それでも解決しない場合、完成版の該当メソッドだけを参照

ただし、まずは自分で実装することを推奨します！完成版を見る前に、TODOコメントとヒントをじっくり読んでください。

## 発展課題

**📚 詳細**: [まとめと発展課題（講義資料05）](docs/lectures/05-summary.md)、[アーキテクチャ解説](docs/architecture.md)

時間が余った場合は、以下の機能を追加してみましょう：

### 1. DELコマンドの実装

キーを削除するコマンド：

```python
async def execute_del(self, *keys: str) -> int:
    """DEL: 1つ以上のキーを削除.

    Returns:
        削除されたキーの数
    """
    # TODO: 実装してください
    pass
```

### 2. EXISTSコマンドの実装

キーの存在確認コマンド：

```python
async def execute_exists(self, *keys: str) -> int:
    """EXISTS: 1つ以上のキーの存在確認.

    Returns:
        存在するキーの数
    """
    # TODO: 実装してください
    pass
```

### 3. EXPIRETIMEコマンドの実装 (Redis 7.0+)

有効期限のUnix timestampを返すコマンド：

```python
async def execute_expiretime(self, key: str) -> int:
    """EXPIRETIME: 有効期限のUnix timestampを取得.

    Returns:
        Unix timestamp
        -1: キーは存在するが有効期限なし
        -2: キーが存在しない
    """
    # TODO: 実装してください
    pass
```

### 4. メトリクスの実装

サーバの統計情報を収集：

```python
class Metrics:
    """サーバのメトリクス収集"""

    def __init__(self) -> None:
        self.total_commands = 0
        self.total_connections = 0
        self.active_connections = 0

    def record_command(self, command_name: str) -> None:
        # TODO: 実装してください
        pass
```

## 参考資料

### 本プロジェクトの学習資料
- [アーキテクチャ解説](docs/architecture.md) - システム全体像、レイヤー構造、設計原則
- [段階別講義資料](docs/lectures/) - 各ステップの理論解説
  - [00-introduction.md](docs/lectures/00-introduction.md) - Redis基礎とRESP入門
  - [01-tcp-server.md](docs/lectures/01-tcp-server.md) - asyncio TCPサーバ
  - [02-protocol-parsing.md](docs/lectures/02-protocol-parsing.md) - RESPプロトコル詳細
  - [03-commands.md](docs/lectures/03-commands.md) - コマンド実装パターン
  - [04-expiry.md](docs/lectures/04-expiry.md) - 有効期限管理
  - [05-summary.md](docs/lectures/05-summary.md) - まとめと発展課題

### 外部資料
- [Redis Protocol specification](https://redis.io/docs/reference/protocol-spec/)
- [Python asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [Real Python: Async IO in Python](https://realpython.com/async-io-python/)

## トラブルシューティング

### テストが失敗する

**問題**: `NotImplementedError` が発生する

**対処法**: TODOコメントのある箇所が未実装です。該当するメソッドを実装してください。

```bash
# どのテストが失敗しているか確認
pytest tests/test_protocol.py -v

# 特定のメソッドだけテスト
pytest tests/test_protocol.py::TestRESPParser::test_encode_simple_string -v
```

### redis-cliが接続できない

1. サーバが起動しているか確認: `python -m mini_redis`
2. ポート6379が使用可能か確認: `lsof -i :6379`
3. `mini_redis/server.py` は実装済みなので、protocol/storage/commands/expiryが正しく実装されているか確認

### テストがタイムアウトする

1. Active Expiryのバックグラウンドタスクが原因の可能性
2. テストで `await asyncio.sleep(0)` を使ってタスク切り替えを確認

### 型チェックエラー

1. `mypy mini_redis` を実行して型エラーを確認
2. 型ヒントを追加: `value: str | None` など

### 完成版コードの使用

どうしても解決できない場合、完成版コードで動作確認できます：

```bash
# サーバを起動
python -m solutions.mini_redis

# 別のターミナルでredis-cliで接続
redis-cli -p 6379
```

詳細は [`solutions/README.md`](solutions/README.md) を参照してください。

## まとめ

**📚 詳細**: [まとめと発展課題（講義資料05）](docs/lectures/05-summary.md)

このワークショップでは、以下を学びました：

1. ✅ **asyncioを使ったTCPサーバの実装パターン**: StreamReader/StreamWriterによる非同期I/O、接続管理
2. ✅ **RESPプロトコルの仕様とパーサの実装**: Arrays/Bulk Stringsのパース、エンコード関数
3. ✅ **基本的なRedisコマンドの動作原理**: PING/GET/SET/INCR/EXPIRE/TTLの実装
4. ✅ **Redisの期限管理メカニズム**: Passive + Active Expirationの2段階管理

### 習得したスキル

- asyncio/awaitによる非同期プログラミング
- バイナリプロトコルの実装
- レイヤー分離設計（Network → Protocol → Command → Storage）
- テストドリブン開発

### 次のステップ

詳細な発展課題は[講義資料05](docs/lectures/05-summary.md)と[アーキテクチャ解説](docs/architecture.md)を参照してください。

- **基本コマンド拡張**: DEL/EXISTS/EXPIRETIME
- **データ永続化**: RDB/AOFの実装
- **トランザクション**: MULTI/EXEC/WATCHの実装
- **Pub/Sub**: PUBLISH/SUBSCRIBEの実装
- **複雑なデータ構造**: List/Hash/Set/Sorted Setの実装
- **メトリクス収集**: コマンド統計、接続数追跡

お疲れ様でした！
