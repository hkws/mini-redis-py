# Project Structure

## ルートディレクトリ構成

```
mini-redis-py/
├── mini_redis/          # 学習者向け実装雛形（TODOコメント付き）
├── solutions/           # 完成版コード（参考用）
├── tests/               # テストスイート
├── .kiro/               # Kiro仕様管理
├── .claude/             # Claude Code設定
├── pyproject.toml       # プロジェクト設定
├── uv.lock              # uvロックファイル
├── README.md            # プロジェクト概要
├── WORKSHOP_GUIDE.md    # ワークショップ実施ガイド
├── CLAUDE.md            # Claude Code用プロジェクト指示
├── CfP.md               # ワークショップ提案書
└── memo.md              # 開発メモ
```

## 主要ディレクトリの詳細

### `mini_redis/` - 学習者向け実装雛形

実装する必要があるコードベース。TODOコメントと実装ヒントが含まれています。

```
mini_redis/
├── __init__.py          # パッケージ初期化
├── __main__.py          # エントリーポイント（実装済み）
├── protocol.py          # RESPプロトコル（要実装）
├── storage.py           # インメモリストレージ（要実装）
├── commands.py          # コマンド実行層（要実装）
├── expiry.py            # 有効期限管理（要実装）
└── server.py            # TCPサーバ（一部実装が必要）
```

**実装順序（推奨）**:
1. `protocol.py` - RESPプロトコルのパース・エンコード
2. `storage.py` - データストレージの基本操作
3. `commands.py` - コマンドルーティングと実行
4. `expiry.py` - 有効期限管理（Passive + Active）
5. `server.py` - クライアント接続処理

### `solutions/` - 完成版コード

学習者が詰まった時の参考用。完全に動作する実装が含まれています。

```
solutions/
├── README.md            # 完成版の使い方
└── mini_redis/          # mini_redis/と同じ構造
    ├── __init__.py
    ├── __main__.py
    ├── protocol.py      # 完成版
    ├── storage.py       # 完成版
    ├── commands.py      # 完成版
    ├── expiry.py        # 完成版
    └── server.py        # 完成版
```

**使用方法**:
```bash
# 完成版を学習者向けディレクトリにコピー
cp -f solutions/mini_redis/*.py mini_redis/

# または、特定ファイルのみコピー
cp solutions/mini_redis/protocol.py mini_redis/protocol.py
```

### `tests/` - テストスイート

各モジュールに対応したテストファイル。実装の正確性を確認します。

```
tests/
├── __init__.py
├── test_imports.py      # インポート可能性のテスト
├── test_protocol.py     # RESPプロトコルのテスト
├── test_storage.py      # ストレージのテスト
├── test_commands.py     # コマンド実行のテスト
├── test_expiry.py       # 有効期限管理のテスト
└── test_server.py       # TCPサーバのテスト
```

**テスト実行例**:
```bash
# 全テスト実行
pytest

# 特定モジュールのテスト
pytest tests/test_protocol.py -v

# 特定のテストクラス
pytest tests/test_protocol.py::TestRESPParser -v
```

### `.kiro/` - Kiro仕様管理

Spec-Driven Developmentの仕様ファイル。

```
.kiro/
├── steering/            # ステアリングドキュメント
│   ├── product.md       # プロダクト概要
│   ├── tech.md          # 技術スタック
│   └── structure.md     # プロジェクト構造（このファイル）
└── specs/               # 機能仕様
    └── mini-redis-py/   # 現在のプロジェクト仕様
        ├── spec.json    # 仕様メタデータ
        ├── requirements.md  # 要件定義
        ├── design.md    # 技術設計
        └── tasks.md     # 実装タスク
```

### `.claude/` - Claude Code設定

```
.claude/
├── commands/            # カスタムスラッシュコマンド
│   └── kiro/           # Kiroコマンド群
│       ├── spec-init.md
│       ├── spec-requirements.md
│       ├── spec-design.md
│       ├── spec-tasks.md
│       ├── spec-impl.md
│       ├── spec-status.md
│       ├── steering.md
│       ├── steering-custom.md
│       ├── validate-design.md
│       └── validate-gap.md
└── settings.local.json  # ローカル設定
```

## コード構成パターン

### モジュール間の依存関係

```
server.py
  ↓ 依存
protocol.py + commands.py
  ↓ 依存
storage.py + expiry.py
```

**依存関係のルール**:
- 上位層は下位層に依存可能
- 下位層は上位層に依存しない（逆依存禁止）
- 同一層内での相互依存は最小限に

### ファイル命名規則

**パッケージファイル**:
- `snake_case.py`: モジュール名（例: `protocol.py`, `storage.py`）
- `__init__.py`: パッケージ初期化
- `__main__.py`: エントリーポイント

**テストファイル**:
- `test_*.py`: テストモジュール（例: `test_protocol.py`）
- テスト対象と同じ名前を使用

**ドキュメント**:
- `UPPERCASE.md`: 重要なドキュメント（例: `README.md`, `WORKSHOP_GUIDE.md`）
- `lowercase.md`: 通常のドキュメント（例: `memo.md`）

### import構成規則

**標準ライブラリ → 外部パッケージ → ローカルモジュールの順**:

```python
# 標準ライブラリ
import asyncio
import time
from typing import Any

# 外部パッケージ（開発時のみ）
import pytest

# ローカルモジュール
from mini_redis.protocol import RESPParser
from mini_redis.storage import Storage
```

**ruffによるimport自動整理**:
```bash
ruff check --fix .  # import順序を自動修正
```

### 主要な実装パターン

#### 1. エラーハンドリング

カスタム例外クラスを使用:

```python
class CommandError(Exception):
    """コマンド実行エラー"""
    pass

class RESPProtocolError(Exception):
    """RESPプロトコルエラー"""
    pass
```

#### 2. 型ヒント

Python 3.12+の型ヒントを活用:

```python
# Union型の新しい書き方
def get(key: str) -> str | None:
    ...

# Genericコレクション
_data: dict[str, str] = {}
_expiry: dict[str, int] = {}
```

#### 3. asyncio実装パターン

**コルーチン定義**:
```python
async def handle_client(reader: StreamReader, writer: StreamWriter) -> None:
    ...
```

**タスク管理**:
```python
# バックグラウンドタスクの起動
self._active_expiry_task = asyncio.create_task(self._active_expiry_loop())

# タスクのキャンセル
if self._active_expiry_task:
    self._active_expiry_task.cancel()
```

#### 4. クリーンアップパターン

**finallyブロックでのリソース解放**:
```python
try:
    # メイン処理
    ...
finally:
    # クリーンアップ（必ず実行される）
    writer.close()
    await writer.wait_closed()
```

## アーキテクチャ原則

### 1. レイヤー分離

各モジュールは明確な責務を持ち、他のレイヤーに依存しない設計:

- **Protocol Layer**: 通信フォーマットのみを扱う
- **Storage Layer**: データの保存・取得のみを扱う
- **Command Layer**: ビジネスロジックを実行
- **Network Layer**: TCP接続管理のみを扱う

### 2. 単一責任の原則

各クラス・関数は1つの責務のみを持つ:

```python
# ✅ 良い例: 1つの責務
def encode_simple_string(value: str) -> bytes:
    """Simple Stringをエンコードする"""
    return f"+{value}\r\n".encode('utf-8')

# ❌ 悪い例: 複数の責務
def encode_and_send_string(value: str, writer: StreamWriter) -> None:
    """エンコードして送信する（責務が混在）"""
    data = f"+{value}\r\n".encode('utf-8')
    writer.write(data)
```

### 3. テスタビリティ

各コンポーネントは独立してテスト可能:

```python
# プロトコル層はストレージに依存しない
parser = RESPParser()
result = await parser.parse_command(reader)

# ストレージ層はネットワークに依存しない
storage = Storage()
storage.set("key", "value")
```

### 4. 明示的なエラーハンドリング

エラーは適切な層で捕捉し、適切なレスポンスを返す:

```python
try:
    result = await self._commands.execute(command)
except CommandError as e:
    response = encode_error(str(e))
except Exception as e:
    response = encode_error("ERR internal server error")
```

## ディレクトリ追加のガイドライン

### 新しいモジュールの追加

将来的な拡張（例: データ永続化）:

```
mini_redis/
├── persistence/         # 新機能: データ永続化
│   ├── __init__.py
│   ├── rdb.py          # RDBフォーマット
│   └── aof.py          # AOFフォーマット
└── ...
```

対応するテストも追加:
```
tests/
├── test_rdb.py
└── test_aof.py
```

### ドキュメントの追加

新しいガイドやチュートリアル:

```
docs/
├── advanced/            # 発展的なトピック
│   ├── persistence.md
│   └── pubsub.md
└── architecture/        # アーキテクチャドキュメント
    └── design_decisions.md
```

### 設定ファイルの追加

プロジェクト設定やCI/CD:

```
.github/
└── workflows/
    ├── test.yml         # CI: テスト実行
    └── lint.yml         # CI: リンター実行
```
