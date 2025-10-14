# Mini-Redis

Pythonによる小さなRedisクローン実装（学習用）

## 概要

Mini-Redisは、60〜90分のワークショップでPython/asyncioを使用してRedisの基本機能を実装する学習プロジェクトです。RESPプロトコル、非同期プログラミング、ネットワークサーバの実装を実践的に学べます。

## 学習目標

- **asyncioによるTCPサーバ**: 非同期I/Oとイベントループの理解
- **RESPプロトコル**: Redisの通信フォーマットの実装
- **基本コマンド**: PING/GET/SET/INCR/EXPIRE/TTLの動作原理
- **有効期限管理**: Passive + Active Expirationの2段階管理

## 学習資料

本プロジェクトには、段階的に学べる充実した学習資料が用意されています：

### 📚 理論学習

- **[アーキテクチャ解説](docs/architecture.md)** - システム全体像、レイヤー構造、設計原則
- **[段階別講義資料](docs/lectures/)** - 各ステップの詳細な理論解説
  - [00-introduction.md](docs/lectures/00-introduction.md) - Redis基礎とRESP入門
  - [01-tcp-server.md](docs/lectures/01-tcp-server.md) - asyncio TCPサーバ
  - [02-protocol-parsing.md](docs/lectures/02-protocol-parsing.md) - RESPプロトコル詳細
  - [03-commands.md](docs/lectures/03-commands.md) - コマンド実装パターン
  - [04-expiry.md](docs/lectures/04-expiry.md) - 有効期限管理
  - [05-summary.md](docs/lectures/05-summary.md) - まとめと発展課題

### 🛠️ 実践ガイド

- **[WORKSHOP_GUIDE.md](WORKSHOP_GUIDE.md)** - 詳細な実装手順、デバッグヒント、トラブルシューティング

**推奨学習フロー**: 講義資料で理論を学ぶ → WORKSHOP_GUIDE.mdで実装 → テストで確認

## プロジェクト構成

```
mini-redis-py/
├── docs/                # 学習資料
│   ├── architecture.md  # アーキテクチャ解説
│   └── lectures/        # 段階別講義資料
├── mini_redis/          # 学習者向け実装雛形（TODOコメント付き）
│   ├── protocol.py      # RESPプロトコル
│   ├── storage.py       # データストレージ
│   ├── commands.py      # コマンド実行層
│   ├── expiry.py        # 有効期限管理
│   └── server.py        # TCPサーバ
├── solutions/           # 完成版コード（参考用）
│   └── mini_redis/      # 完全に動作する実装
├── tests/               # テストスイート
└── WORKSHOP_GUIDE.md    # 実装ガイド
```

詳細なアーキテクチャは [docs/architecture.md](docs/architecture.md) を参照してください。

## クイックスタート

### 1. セットアップ

```bash
# リポジトリをクローン
git clone <repository-url>
cd mini-redis-py

# 開発用ツールを含めてインストール
pip install -e ".[dev]"
```

### 2. 学習開始

```bash
# 講義資料で理論を学ぶ
cat docs/lectures/00-introduction.md

# ワークショップガイドで実装を開始
cat WORKSHOP_GUIDE.md
```

### 3. 実装とテスト

```bash
# TODOコメントを実装
# mini_redis/protocol.py, storage.py, commands.py, expiry.py, server.py

# テストで確認
pytest tests/test_protocol.py -v

# サーバを起動
python -m mini_redis
```

詳細な実装手順は [WORKSHOP_GUIDE.md](WORKSHOP_GUIDE.md) を参照してください。

## 実装コマンド

- `PING`: 接続確認
- `GET <key>`: 値の取得
- `SET <key> <value>`: 値の設定
- `INCR <key>`: 値を1増加
- `EXPIRE <key> <seconds>`: 有効期限の設定
- `TTL <key>`: 残り有効秒数の取得

## ワークショップの流れ

本ワークショップは6つのステップで構成されています（合計60〜90分）：

0. **導入とデモ確認** (5分) - Redis基礎、RESPプロトコル入門
1. **TCPサーバ実装** (15分) - asyncioによるネットワーク層
2. **RESPプロトコル実装** (15分) - パース・エンコード機能
3. **データストレージ実装** (15分) - インメモリキー・バリューストア
4. **コマンド実行層実装** (20分) - PING/GET/SET/INCR/EXPIRE/TTL
5. **有効期限管理実装** (20分) - Passive + Active Expiry
6. **統合テストと振り返り** (10分) - redis-cliで動作確認

詳細は [WORKSHOP_GUIDE.md](WORKSHOP_GUIDE.md) を参照してください。

## 開発ツール

```bash
# すべてのテストを実行
pytest

# 型チェック
mypy mini_redis

# リンター・フォーマッター
ruff check .
ruff format .
```

## トラブルシューティング

実装中に詰まった場合：

1. **[WORKSHOP_GUIDE.md](WORKSHOP_GUIDE.md)** の「よくある間違いと対処法」を確認
2. **テストコード**で期待される動作を確認
3. **[solutions/](solutions/)** ディレクトリの完成版コードを参照

詳細なデバッグ方法とトラブルシューティングは [WORKSHOP_GUIDE.md](WORKSHOP_GUIDE.md) を参照してください。

## 発展課題

基本実装が完了したら、以下に挑戦してみましょう：

- **基本コマンド拡張**: DEL/EXISTS/EXPIRETIME
- **複雑なデータ構造**: List/Hash/Set/Sorted Set
- **データ永続化**: RDB/AOFフォーマット
- **Pub/Sub機能**: PUBLISH/SUBSCRIBE/UNSUBSCRIBE
- **トランザクション**: MULTI/EXEC/WATCH

詳細は [WORKSHOP_GUIDE.md](WORKSHOP_GUIDE.md) と [docs/lectures/05-summary.md](docs/lectures/05-summary.md) を参照してください。

## ライセンス

MIT
