# Mini-Redis

Pythonによる小さなRedisクローン実装（学習用）

## 概要

Mini-Redisは、60〜90分のワークショップでPython/asyncioを使用してRedisの基本機能を実装する学習プロジェクトです。

## 学習目標

- asyncioを使ったTCPサーバの実装パターンを習得
- RESPプロトコルの仕様を理解し、パーサを実装
- 基本的なRedisコマンド（PING/GET/SET/INCR）の動作原理を理解
- Redisの期限管理メカニズム（passive + active expiration）を実装

## セットアップ

```bash
# 開発用ツールを含めてインストール
pip install -e ".[dev]"
```

## 実装コマンド

- `PING`: 接続確認
- `GET <key>`: 値の取得
- `SET <key> <value>`: 値の設定
- `INCR <key>`: 値を1増加
- `EXPIRE <key> <seconds>`: 有効期限の設定
- `TTL <key>`: 残り有効秒数の取得

## テスト実行

```bash
# すべてのテストを実行
pytest

# 型チェック
mypy mini_redis

# リンター・フォーマッター
ruff check .
ruff format .
```

## ライセンス

MIT
