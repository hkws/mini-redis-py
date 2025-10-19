# Mini-Redisアーキテクチャ

## 概要

このドキュメントでは、Mini-Redisのシステムアーキテクチャ、レイヤー構造、モジュール間の依存関係、設計原則について詳しく解説します。

Mini-Redisは、レイヤー分離アーキテクチャを採用し、各レイヤーが明確な責務を持つことで、テスタビリティとメンテナンス性を向上させています。

## システム全体像

以下の図は、Mini-Redisのシステム全体像を示しています：

```mermaid
graph TB
    CLI[Redis Client<br/>redis-cli] -->|RESP Protocol| SERVER[Network Layer<br/>server.py]
    SERVER -->|parse| PROTOCOL[Protocol Layer<br/>protocol.py]
    PROTOCOL -->|command array| SERVER
    SERVER -->|execute| COMMANDS[Command Layer<br/>commands.py]
    COMMANDS -->|get/set/delete| STORAGE[Storage Layer<br/>storage.py]
    COMMANDS -->|check/set expiry| EXPIRY[Expiry Manager<br/>expiry.py]
    EXPIRY -->|delete expired| STORAGE

    style CLI fill:#e1f5ff
    style SERVER fill:#fff4e1
    style PROTOCOL fill:#ffe1f5
    style COMMANDS fill:#e1ffe1
    style STORAGE fill:#f5e1ff
    style EXPIRY fill:#ffe1e1
```

### 主要コンポーネント

| コンポーネント | ファイル | 責務 |
|--------------|---------|------|
| **Redis Client** | - | RESPプロトコルでコマンドを送信 |
| **Network Layer** | `server.py` | TCP接続管理、クライアント処理ループ |
| **Protocol Layer** | `protocol.py` | RESPメッセージのパース・エンコード |
| **Command Layer** | `commands.py` | コマンドルーティング、コマンド処理 |
| **Storage Layer** | `storage.py` | キー・バリュー操作、データ保存 |
| **Expiry Manager** | `expiry.py` | 有効期限管理（Passive + Active Expiry） |


## データフロー

### GETコマンドのシーケンス図

以下は、`GET mykey`コマンドを実行した際のデータフローです：

```mermaid
sequenceDiagram
    participant Client as Redis Client
    participant Server as server.py
    participant Protocol as protocol.py
    participant Commands as commands.py
    participant Expiry as expiry.py
    participant Storage as storage.py

    Client->>Server: *2\r\n$3\r\nGET\r\n$5\r\nmykey\r\n
    Note over Server: TCP接続受付

    Server->>Protocol: parse_command(reader)
    Protocol->>Protocol: 配列をパース
    Protocol->>Protocol: Bulk Stringsをパース
    Protocol-->>Server: ["GET", "mykey"]

    Server->>Commands: execute(["GET", "mykey"])
    Note over Commands: ルーティング: _get()

    Commands->>Expiry: check_and_remove_expired("mykey")
    Expiry->>Storage: get_expiry("mykey")
    Storage-->>Expiry: 1234567890 (timestamp)
    Expiry->>Expiry: 現在時刻と比較

    alt 期限切れ
        Expiry->>Storage: delete("mykey")
        Expiry-->>Commands: True (削除済み)
        Commands-->>Server: None
    else 期限内
        Expiry-->>Commands: False (期限内)
        Commands->>Storage: get("mykey")
        Storage-->>Commands: "value"
        Commands-->>Server: "value"
    end

    Server->>Protocol: encode_bulk_string("value")
    Protocol-->>Server: $5\r\nvalue\r\n

    Server->>Client: $5\r\nvalue\r\n
    Note over Client: 結果を表示
```

### SETコマンドのシーケンス図

```mermaid
sequenceDiagram
    participant Client as Redis Client
    participant Server as server.py
    participant Protocol as protocol.py
    participant Commands as commands.py
    participant Storage as storage.py

    Client->>Server: *3\r\n$3\r\nSET\r\n$5\r\nmykey\r\n$5\r\nvalue\r\n

    Server->>Protocol: parse_command(reader)
    Protocol-->>Server: ["SET", "mykey", "value"]

    Server->>Commands: execute(["SET", "mykey", "value"])
    Note over Commands: ルーティング: _set()

    Commands->>Storage: set("mykey", "value")
    Storage->>Storage: _data["mykey"] = "value"
    Storage-->>Commands: (完了)

    Commands-->>Server: "OK"

    Server->>Protocol: encode_simple_string("OK")
    Protocol-->>Server: +OK\r\n

    Server->>Client: +OK\r\n
```

### Active Expiryのフロー

```mermaid
graph TB
    START[起動] --> INIT[ExpiryManager初期化]
    INIT --> TASK[create_task<br/>_active_expiry_loop]
    TASK --> LOOP[無限ループ開始]
    LOOP --> SLEEP[1秒待機]
    SLEEP --> SAMPLE[ランダム20キーサンプリング]
    SAMPLE --> CHECK[各キーをチェック]
    CHECK --> EXPIRED{期限切れ?}

    EXPIRED -->|はい| DELETE[キーを削除]
    EXPIRED -->|いいえ| NEXT{次のキー?}

    DELETE --> NEXT
    NEXT -->|ある| CHECK
    NEXT -->|ない| RATE{削除率 > 25%?}

    RATE -->|はい| SAMPLE
    RATE -->|いいえ| LOOP

    CANCEL[キャンセル要求] --> CLEANUP[クリーンアップ]
    CLEANUP --> END[終了]

    style START fill:#e1f5ff
    style LOOP fill:#e1ffe1
    style EXPIRED fill:#fff4e1
    style RATE fill:#fff4e1
    style DELETE fill:#ffe1e1
    style END fill:#ffe1e1
```

