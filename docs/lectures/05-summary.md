# まとめと次のステップ

## おめでとうございます！

Mini-Redisワークショップを完走しました！　asyncio、RESPプロトコル実装などを習得できたはずです。

所要時間: 約5分

## 実装した機能の振り返り

### 1. RESPプロトコルのパース・エンコード

実装内容:
5つのRESPデータ型のパース（Simple Strings, Errors, Integers, Bulk Strings, Arrays）、コマンド配列のパース（`GET mykey` → `["GET", "mykey"]`）、そして応答のエンコード（Pythonオブジェクト → RESPバイト列）を実装しました。

学んだ概念:
バイナリセーフな通信、長さ指定によるデータ区切り、そしてCRLF終端とバイト長計算について学びました。


### 2. asyncio TCPサーバ

実装内容:
`asyncio.start_server()`によるTCPサーバ構築、StreamReader/StreamWriterによるデータ送受信、複数クライアントの並行処理、そしてクリーンアップを実装しました。

学んだ概念:
イベントループとコルーチン、`async`/`await`構文、そして非同期I/Oの利点について学びました。

### 3. 6つの基本コマンド

実装内容:
PING（接続確認）、GET（値取得）、SET（値設定）、INCR（インクリメント）、EXPIRE（期限設定）、TTL（残り時間取得）の6つのコマンドを実装しました。それぞれ、引数の有無で応答を変える方法、Null値の扱い、型チェック、エラーハンドリング、Unixタイムスタンプの計算などを学びました。

学んだ概念:
コマンドルーティング、引数検証、エラーメッセージの形式、そしてビジネスロジックの分離について学びました。


### 4. 2段階有効期限管理

実装内容:
Passive Expiry（コマンド実行時の期限チェック）、Active Expiry（バックグラウンドでのランダムサンプリング）、そしてasyncioバックグラウンドタスクを実装しました。

学んだ概念:
ランダムサンプリングによる削除アルゴリズム、削除率による適応的実行、そしてタスクのライフサイクル管理について学びました。


## 統合テストと動作確認

すべての実装が完了したら、Mini-Redisを起動して動作確認しましょう！（目安時間: 10分）

### 1. サーバを起動

```bash
python -m mini_redis
```

### 2. redis-cliで接続

別のターミナルで：

```bash
redis-cli -p 6379
```

### 3. 基本コマンドをテスト

```bash
# 接続確認
> PING
PONG

# 基本操作
> SET mykey "hello"
OK

> GET mykey
"hello"

# カウンター
> INCR counter
(integer) 1

> INCR counter
(integer) 2

> INCR counter
(integer) 3

> GET counter
"3"
```

### 4. 有効期限をテスト

```bash
# 10秒の期限を設定
> SET temp "data"
OK

> EXPIRE temp 10
(integer) 1

> TTL temp
(integer) 9

# 10秒後にアクセス
> GET temp
(nil)  # Active Expiryで削除済み
```

### 5. エラーケースをテスト

```bash
# 引数数エラー
> GET
(error) ERR wrong number of arguments for 'get' command

# 未知のコマンド
> HELLO
(error) ERR unknown command 'HELLO'

# 型エラー
> SET text "not a number"
OK

> INCR text
(error) ERR value is not an integer or out of range
```

### 学習内容の振り返り

ここまでで、以下を習得しました：

- ✅ asyncioを使ったTCPサーバの実装パターン
- ✅ RESPプロトコルの仕様とパーサの実装
- ✅ 基本的なRedisコマンドの動作原理
- ✅ Redisの期限管理メカニズム（Passive + Active Expiration）

おめでとうございます！Mini-Redisワークショップ完走です！

## 発展課題

Mini-Redisの基本機能は完成しましたが、さらに学びを深めるために、以下のような発展課題に取り組むと良いかもしれません。

### レベル1: 基本コマンドの拡張

#### DELコマンド

目的: キーを削除する

構文: `DEL key [key ...]`

応答: 削除したキーの数（Integer）

実装のヒント:
- 複数のキーを受け取る
- 各キーを削除し、成功した数をカウント
- 存在しないキーはカウントしない

ドキュメント: [https://redis.io/docs/latest/commands/del/](https://redis.io/docs/latest/commands/del/)

#### EXISTSコマンド

目的: キーが存在するかチェック

構文: `EXISTS key [key ...]`

応答: 存在するキーの数（Integer）

実装のヒント:
- Passive Expiryチェックを忘れずに
- 複数キーに対応

ドキュメント: [https://redis.io/docs/latest/commands/exists/](https://redis.io/docs/latest/commands/exists/)

### レベル2: より複雑なデータ構造に対応

#### Listの実装

コマンド: `LPUSH`, `RPUSH`, `LPOP`, `RPOP`, `LRANGE`

データ構造:

```python
_lists: dict[str, list[str]] = {}
```

実装のヒント:
- Pythonのリスト（`list`）をそのまま使用
- `LRANGE`でスライスを返す

ドキュメント:
- LPUSH: https://redis.io/docs/latest/commands/lpush/

#### Hashの実装

コマンド: `HSET`, `HGET`, `HGETALL`, `HDEL`

データ構造:

```python
_hashes: dict[str, dict[str, str]] = {}
```

実装のヒント:
- ネストした辞書構造
- `HGETALL`でフィールドと値のペアを返す

### レベル3: データ永続化

#### RDB（Redis Database）形式

目的: スナップショット形式でデータを保存

ヒント:
- [SAVEコマンド](https://redis.io/docs/latest/commands/save/)を実装
- 定期的にバックグラウンドでスナップショットを保存
- 起動時にRDBファイルを読み込み

ドキュメント：https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/#snapshotting


#### AOF（Append-Only File）形式

目的: コマンドログ形式でデータを保存

ヒント:
- 書き込みコマンド（SET, DEL等）をファイルに追記
- 起動時にコマンドを再実行してデータを復元
- RESPフォーマットでコマンドを保存

ドキュメント: https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/#append-only-file

## 最後に

Mini-Redisワークショップを通じて、asyncioによる非同期プログラミングの実践や、ネットワークプロトコル（RESP）の実装についての基礎を習得しました。

みなさん一度は聞いた/使ったことがあるであろうRedisというプロダクトの中心的な機能が、RESPという意外とシンプルな仕組みで動いていることを理解できたのではないでしょうか。

このように、普段は当たり前に使っている機能の裏側がどうなっているのかを探ることは、非常に面白く自身のスキルアップにも繋がることもあります。ぜひみなさんのお気に入りのプロダクトや機能の裏側も深掘りしてみてください。

