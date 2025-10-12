# Mini-Redis

Pythonによる小さなRedisクローン実装（学習用）

## 概要

Mini-Redisは、60〜90分のワークショップでPython/asyncioを使用してRedisの基本機能を実装する学習プロジェクトです。

## 学習目標

- asyncioを使ったTCPサーバの実装パターンを習得
- RESPプロトコルの仕様を理解し、パーサを実装
- 基本的なRedisコマンド（PING/GET/SET/INCR）の動作原理を理解
- Redisの期限管理メカニズム（passive + active expiration）を実装

## プロジェクト構成

```
mini-redis-py/
├── mini_redis/          # 学習者向け実装雛形（TODOコメント付き）
│   ├── protocol.py      # RESPプロトコルのパース・エンコード
│   ├── storage.py       # インメモリキー・バリューストア
│   ├── commands.py      # コマンド実行層
│   ├── expiry.py        # 有効期限管理（Passive + Active）
│   └── server.py        # TCPサーバ（一部実装が必要）
├── solutions/           # 完成版コード（参考用）
│   └── mini_redis/      # 完全に動作する実装
├── tests/               # テストスイート
└── WORKSHOP_GUIDE.md    # ワークショップ実施ガイド
```

## セットアップ

```bash
# リポジトリをクローン
git clone <repository-url>
cd mini-redis-py

# 開発用ツールを含めてインストール
pip install -e ".[dev]"
```

## クイックスタート

### ステップ1: 実装を開始

`mini_redis/` ディレクトリのファイルにあるTODOコメントを順番に実装していきます。

```bash
# ワークショップガイドを開く
cat WORKSHOP_GUIDE.md

# エディタで実装を開始
# 推奨順序: protocol.py → storage.py → commands.py → expiry.py
```

### ステップ2: テストで確認

```bash
# 特定のモジュールのテストを実行
pytest tests/test_protocol.py -v

# すべてのテストを実行
pytest
```

### ステップ3: 完成版を参考にする

詰まった場合は、`solutions/` ディレクトリの完成版コードを参考にできます。

```bash
# 実装と完成版を比較
diff mini_redis/protocol.py solutions/mini_redis/protocol.py
```

## 実装コマンド

- `PING`: 接続確認
- `GET <key>`: 値の取得
- `SET <key> <value>`: 値の設定
- `INCR <key>`: 値を1増加
- `EXPIRE <key> <seconds>`: 有効期限の設定
- `TTL <key>`: 残り有効秒数の取得

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

## ワークショップの流れ

1. **RESPプロトコルの実装** (20分) - `mini_redis/protocol.py`
2. **データストレージの実装** (15分) - `mini_redis/storage.py`
3. **コマンド実行層の実装** (20分) - `mini_redis/commands.py`
4. **有効期限管理の実装** (15分) - `mini_redis/expiry.py`
5. **ネットワーク層の実装** (15分) - `mini_redis/server.py`
6. **統合テストと動作確認** (10分) - redis-cliで接続

詳細は [`WORKSHOP_GUIDE.md`](WORKSHOP_GUIDE.md) を参照してください。

## 完成版コードの使用

完成版コードで動作確認したい場合：

```bash
# 完成版をmini_redis/にコピー
cp -f solutions/mini_redis/*.py mini_redis/

# サーバを起動
python -m mini_redis

# 別のターミナルでredis-cliで接続
redis-cli -p 6379
```

詳細は [`solutions/README.md`](solutions/README.md) を参照してください。

## トラブルシューティング

### テストが失敗する

`NotImplementedError` が発生する場合、TODOコメントのある箇所が未実装です。該当するメソッドを実装してください。

### redis-cliが接続できない

1. サーバが起動しているか確認
2. ポート6379が使用可能か確認: `lsof -i :6379`
3. `mini_redis/server.py` が実装されているか確認

### 詰まった場合

1. `WORKSHOP_GUIDE.md` の「よくある間違い」セクションを確認
2. テストコードで期待される動作を確認
3. `solutions/` ディレクトリの完成版コードを参照

## 発展課題

すべての実装が完了したら、以下に挑戦してみましょう：

- DEL / EXISTS コマンドの実装
- EXPIRETIME コマンドの実装（Redis 7.0+）
- メトリクス収集機能の追加
- Pub/Sub機能の実装

詳細は `WORKSHOP_GUIDE.md` の「発展課題」セクションを参照してください。

## ライセンス

MIT
