# Mini-Redis 完成版コード

このディレクトリには、Mini-Redisワークショップの完成版実装が含まれています。

## 概要

学習者がワークショップで実装する目標となる、完全に動作するMini-Redisの実装です。

## ファイル一覧

### 1. protocol.py
RESPプロトコルのパース・エンコード機能の完成版

**主要機能**:
- `parse_command()`: RESP形式のコマンドをパース
- `encode_simple_string()`: Simple Stringのエンコード
- `encode_error()`: エラーメッセージのエンコード
- `encode_integer()`: 整数のエンコード
- `encode_bulk_string()`: Bulk Stringのエンコード

### 2. storage.py
インメモリキー・バリューストアの完成版

**主要機能**:
- `get()` / `set()`: 基本的なキー・バリュー操作
- `delete()` / `exists()`: キーの削除と存在確認
- `set_expiry()` / `get_expiry()`: 有効期限の管理
- `get_all_keys()`: すべてのキーの取得（Active expiry用）

### 3. commands.py
コマンド実行層の完成版

**実装コマンド**:
- `PING`: 接続確認
- `GET` / `SET`: 値の取得・設定
- `INCR`: 値の1増加
- `EXPIRE`: 有効期限の設定
- `TTL`: 残り有効秒数の取得

### 4. expiry.py
有効期限管理機能の完成版

**主要機能**:
- **Passive expiry**: `check_and_remove_expired()` - アクセス時に期限をチェック
- **Active expiry**: バックグラウンドタスクで定期的にランダムサンプリング
- 削除率が25%を超えたら即座に次のサンプリング

## 使い方

### 完成版を実行

完成版コードを使ってサーバを起動したい場合：

```bash
# 1. 完成版をmini_redis/にコピー
cp -f solutions/mini_redis/*.py mini_redis/

# 2. サーバを起動
python -m mini_redis

# 3. 別のターミナルでredis-cliで接続
redis-cli -p 6379
```

### 実装と比較

学習者が実装したコードと完成版を比較する場合：

```bash
# 特定のファイルを比較
diff mini_redis/protocol.py solutions/mini_redis/protocol.py

# または、diffツールを使用
code --diff mini_redis/protocol.py solutions/mini_redis/protocol.py
```

### 実装の参考

詰まった場合は、以下の順序で参照することを推奨：

1. **ワークショップガイド**: `WORKSHOP_GUIDE.md` の「よくある間違い」セクション
2. **テストコード**: `tests/` ディレクトリのテストで期待される動作を確認
3. **完成版コード**: このディレクトリの該当ファイルを参照

## 注意事項

- 完成版コードをそのままコピーするのではなく、まずは自分で実装することを推奨します
- 詰まった箇所の参考として、該当するメソッドだけを参照することをお勧めします
- 完成版コードにも学習用のコメントが含まれているため、理解を深めるのに役立ちます

## 実装のポイント

### RESPプロトコル (protocol.py)

```python
# Bulk Stringの長さはバイト数で指定
value_bytes = value.encode('utf-8')
length = len(value_bytes)  # 文字数ではなくバイト数
```

### Passive Expiry (commands.py)

```python
# GET/INCR/EXPIRE/TTLの最初で必ず呼び出す
async def execute_get(self, key: str) -> str | None:
    self._expiry.check_and_remove_expired(key)  # Passive expiry
    return self._store.get(key)
```

### Active Expiry (expiry.py)

```python
# 削除率が25%を超えたら即座に次のサンプリング
while True:
    # サンプリングと削除
    deletion_rate = (deleted_count / sample_size) * 100
    if deletion_rate <= 25:
        break  # 削除率が低いので終了
```

## テストの実行

完成版コードが正しく動作することを確認：

```bash
# すべてのテストを実行
pytest

# 特定のモジュールのテストだけ実行
pytest tests/test_protocol.py -v
pytest tests/test_storage.py -v
pytest tests/test_commands.py -v
pytest tests/test_expiry.py -v

# 型チェック
mypy solutions/mini_redis

# リンター・フォーマッター
ruff check solutions/mini_redis
```

## さらなる学習

完成版を理解したら、以下の発展課題に挑戦してみましょう：

1. **DEL / EXISTS コマンドの実装**
2. **EXPIRETIME コマンドの実装**（Redis 7.0+）
3. **メトリクス収集機能の追加**
4. **Pub/Sub機能の実装**（設計書を参照）

詳細は`WORKSHOP_GUIDE.md`の「発展課題」セクションを参照してください。
