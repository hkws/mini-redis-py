# Mini-Redis 完成版コード

このディレクトリには、Mini-Redisワークショップの完成版実装が含まれています。

## 概要

学習者がワークショップで実装する目標となる、完全に動作するMini-Redisの実装です。

このディレクトリのコードは相対インポート（`from .module`）を使用しているため、プロジェクトルートの学習用`mini_redis`とは**完全に独立**して動作します。ファイルの移動やコピーなしに、`python -m solutions.mini_redis`で直接実行できます。

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

完成版コードは**ファイルの移動やコピーなし**で直接実行できます。
`solutions/mini_redis`内のコードは相対インポートを使用しているため、学習用の`mini_redis`とは完全に独立して動作します。

```bash
# 完成版を直接起動（ファイルのコピー不要！）
uv run python -m solutions.mini_redis

# 別のターミナルでredis-cliで接続
redis-cli -p 6379
```

**補足**: `python`コマンドが利用可能な環境では、以下のコマンドでも起動できます：

```bash
python -m solutions.mini_redis
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

1. **テストコード**: `tests/` ディレクトリのテストで期待される動作を確認
2. **完成版コード**: このディレクトリの該当ファイルを参照

## 注意事項

- 完成版コードをそのままコピーするのではなく、まずは自分で実装することを推奨します
- 詰まった箇所の参考として、該当するメソッドだけを参照することをお勧めします
- 完成版コードにも学習用のコメントが含まれているため、理解を深めるのに役立ちます
