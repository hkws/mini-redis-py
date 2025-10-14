# Technology Stack

## アーキテクチャ

Mini-Redisは、シンプルな階層型アーキテクチャを採用しています：

```
[Redis Client (redis-cli)]
         ↓
[Network Layer (server.py)] ← TCPサーバ、接続管理
         ↓
[Protocol Layer (protocol.py)] ← RESPプロトコルのパース・エンコード
         ↓
[Command Layer (commands.py)] ← コマンドルーティングと実行
         ↓
[Storage Layer (storage.py)] ← インメモリキー・バリューストア
         ↑
[Expiry Manager (expiry.py)] ← 有効期限管理（Passive + Active）
```

## コア技術スタック

### 言語・ランタイム
- **Python 3.12以上**: 最新の型ヒント機能を活用
- **asyncio**: 非同期I/O、TCPサーバ、並行処理

### ランタイム依存なし
プロジェクトは標準ライブラリのみで動作し、外部ランタイム依存はありません：
- `asyncio`: TCPサーバとプロトコル実装
- `time`: タイムスタンプ管理
- `random`: Active Expiryのサンプリング

## 開発環境

### 必須ツール
- **Python 3.12以上**: `python --version`で確認
- **pip/uv**: パッケージ管理（uvが推奨）

### 開発用依存関係
- **pytest >=8.0.0**: テストフレームワーク
- **pytest-asyncio >=0.23.0**: asyncioテストサポート
- **mypy >=1.8.0**: 型チェッカー（strict mode）
- **ruff >=0.2.0**: リンター・フォーマッター（高速）
- **types-setuptools >=69.0.0**: 型スタブ

### ビルドシステム
- **setuptools >=68.0.0**: パッケージビルド
- **wheel**: ホイールビルドサポート

## 主要コマンド

### セットアップ
```bash
# 開発用ツールを含めてインストール
pip install -e ".[dev]"

# または、uv使用時
uv pip install -e ".[dev]"
```

### テスト実行
```bash
# 全テスト実行
pytest

# 特定モジュールのテスト
pytest tests/test_protocol.py -v

# 特定のテストクラス
pytest tests/test_protocol.py::TestRESPParser -v

# 特定のテストメソッド
pytest tests/test_protocol.py::TestRESPParser::test_parse_simple_command -v

# カバレッジ測定
pytest --cov=mini_redis --cov-report=html
```

### 型チェック
```bash
# 全ファイルの型チェック
mypy mini_redis

# 特定ファイルのみ
mypy mini_redis/protocol.py
```

### リンター・フォーマッター
```bash
# コードチェック
ruff check .

# 自動修正
ruff check --fix .

# フォーマット
ruff format .

# チェックとフォーマットを両方実行
ruff check . && ruff format .
```

### サーバ起動
```bash
# Mini-Redisサーバを起動（デフォルト: ポート6379）
python -m mini_redis

# redis-cliで接続（別のターミナルで）
redis-cli -p 6379
```

### 完成版コードの使用
```bash
python -m solutions.mini_redis
```

## 環境変数

現時点では環境変数による設定は不要です。将来的に以下のような設定が追加される可能性があります：

```bash
# （将来的な拡張例）
MINI_REDIS_PORT=6379          # サーバポート
MINI_REDIS_HOST=127.0.0.1     # バインドアドレス
MINI_REDIS_LOG_LEVEL=INFO     # ログレベル
```

## ポート設定

- **6379**: Mini-Redisサーバのデフォルトポート（本家Redisと同じ）
  - 衝突回避: 本家Redisが起動している場合は停止するか、別ポートを使用
- **16379**: 完成版Mini-Redisサーバのデフォルトポート

## pytest設定

### テストマーカー
- `@pytest.mark.unit`: ユニットテスト（個別コンポーネント）
- `@pytest.mark.integration`: 統合テスト（コンポーネント間の連携）
- `@pytest.mark.e2e`: End-to-Endテスト（実際のTCP接続）

### asyncioモード
- 自動モード有効（`asyncio_mode = "auto"`）
- `async def test_*`が自動的にasyncioで実行

### テストオプション
```bash
# マーカーでフィルタリング
pytest -m unit              # ユニットテストのみ
pytest -m "not e2e"         # E2Eテスト以外

# 詳細表示
pytest -v                   # 詳細表示
pytest -vv                  # より詳細表示
pytest --tb=short          # トレースバックを短縮
```

## mypy設定（Strict Mode）

### Strictモード有効
- `disallow_untyped_defs`: 型ヒントなし関数を禁止
- `disallow_incomplete_defs`: 不完全な型定義を禁止
- `no_implicit_optional`: 暗黙のOptionalを禁止
- `strict_equality`: 厳密な等価性チェック

### 推奨される型ヒント例
```python
# 関数の型ヒント
def get(key: str) -> str | None:
    ...

async def execute(command: list[str]) -> str | int | None:
    ...

# 属性の型ヒント
_data: dict[str, str]
_expiry: dict[str, int]
```

## ruff設定

### 有効なルール
- **E/W**: pycodestyleエラー・警告
- **F**: pyflakes（未使用変数、importなど）
- **I**: isort（import順序）
- **B**: flake8-bugbear（バグを生みやすいコード）
- **C4**: flake8-comprehensions（内包表記）
- **UP**: pyupgrade（Python 3.12+の機能）
- **ARG**: 未使用引数
- **SIM**: 簡潔化可能なコード

### スタイル設定
- 行長: 100文字
- クオート: ダブルクォート
- インデント: スペース4つ
- 改行: 自動検出

## デバッグツール

### ログ出力
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug(f"Command: {command}")
```

### asyncioデバッグモード
```python
import asyncio

asyncio.run(main(), debug=True)
```

### バイト列デバッグ
```python
# repr()でバイト列を可視化
print(f"Received: {line!r}")
# 出力例: Received: b'*2\r\n'
```

## パフォーマンス特性

### 設計上の制約
- **シングルスレッド**: asyncioイベントループ1つで動作
- **インメモリストア**: データは永続化されず、再起動で消失
- **同期的なコマンド実行**: 各コマンドは順次実行（トランザクションなし）

### Active Expiryパラメータ
- サンプリング間隔: 1秒
- サンプルサイズ: 20キー（ランダム）
- 再実行閾値: 削除率25%超
