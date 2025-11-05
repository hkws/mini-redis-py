"""Command handler for Mini-Redis.

このモジュールは、Redisコマンドのルーティングと実行、
およびPassive expiryの統合を担当します。

"""

import time
from solutions.mini_redis.protocol import SimpleString, Integer, BulkString, RedisError, Array


class CommandHandler:
    """Redisコマンドのハンドラ.

    責務:
    - コマンドのルーティングと実行
    - ビジネスロジックの調整
    - Passive expiryの実行

    実装のヒント:
    1. execute(): コマンド名から適切なexecute_*メソッドにルーティング
    2. 各コマンドメソッド: 対応するRedisコマンドの処理を実装
    3. GET/INCR/EXPIRE/TTL: 最初にcheck_and_remove_expired()を呼び出す
    """

    def __init__(self, store, expiry) -> None:
        """ハンドラを初期化.

        Args:
            store: DataStoreのインスタンス
            expiry: ExpiryManagerのインスタンス

        """
        self._store = store
        self._expiry = expiry

    async def execute(self, command: list[str]) -> SimpleString | BulkString | Integer | RedisError | Array:
        """コマンドを実行する"""
        if not command:
            raise CommandError("ERR empty command")

        # コマンド名を大文字に正規化
        cmd_name = command[0].upper()
        args = command[1:]

        # ルーティング
        if cmd_name == "PING":
            return await self.execute_ping(args)
        elif cmd_name == "GET":
            return await self.execute_get(args)
        elif cmd_name == "SET":
            return await self.execute_set(args)
        elif cmd_name == "INCR":
            return await self.execute_incr(args)
        elif cmd_name == "EXPIRE":
            return await self.execute_expire(args)
        elif cmd_name == "TTL":
            return await self.execute_ttl(args)
        else:
            raise CommandError(f"ERR unknown command '{cmd_name}'")

    async def execute_ping(self, args: list[str]) -> SimpleString | BulkString:
        """PINGコマンドを実行"""
        if len(args) == 0:
            # 引数なし: PONGを返す（Simple String）
            return SimpleString("PONG")
        elif len(args) == 1:
            # 引数あり: メッセージをエコーバック（Bulk String）
            return BulkString(args[0])
        else:
            # 引数が多すぎる
            raise CommandError("ERR wrong number of arguments for 'ping' command")

    async def execute_get(self, args: list[str]) -> BulkString:
        """GETコマンドを実行"""
        # 引数検証
        if len(args) != 1:
            raise CommandError("ERR wrong number of arguments for 'get' command")

        key = args[0]

        # Passive Expiry: 期限切れチェック
        if self._expiry.check_and_remove_expired(key):
            return BulkString(None)

        # 値を取得（BulkStringでラップ）
        return BulkString(self._store.get(key))

    async def execute_set(self, args: list[str]) -> SimpleString:
        """SETコマンドを実行"""
        # 引数検証
        if len(args) != 2:
            raise CommandError("ERR wrong number of arguments for 'set' command")

        key = args[0]
        value = args[1]

        # 値を設定
        self._store.set(key, value)

        return SimpleString("OK")

    async def execute_incr(self, args: list[str]) -> Integer:
        """INCRコマンドを実行"""
        # 引数検証
        if len(args) != 1:
            raise CommandError("ERR wrong number of arguments for 'incr' command")

        key = args[0]

        # Passive Expiry: 期限切れチェック
        if self._expiry.check_and_remove_expired(key):
            self._store.set(key, "1")
            return Integer(1)

        # 現在の値を取得
        current = self._store.get(key)

        if current is None:
            # キーが存在しない: 0から開始
            self._store.set(key, "1")
            return Integer(1)

        # 整数に変換を試みる
        try:
            value = int(current)
        except ValueError:
            raise CommandError("ERR value is not an integer or out of range")

        # インクリメント
        new_value = value + 1
        self._store.set(key, str(new_value))

        return Integer(new_value)

    async def execute_expire(self, args: list[str]) -> Integer:
        """EXPIREコマンドを実行"""
        # 引数検証
        if len(args) != 2:
            raise CommandError("ERR wrong number of arguments for 'expire' command")

        key = args[0]

        # 秒数を整数に変換
        try:
            seconds = int(args[1])
        except ValueError:
            raise CommandError("ERR value is not an integer or out of range")

        # Passive Expiry: 期限切れチェック
        if self._expiry.check_and_remove_expired(key):
            return Integer(0)

        # 負の秒数はエラー
        if seconds < 0:
            raise CommandError("ERR invalid expire time in 'expire' command")

        # キーが存在するかチェック
        if self._store.get(key) is None:
            return Integer(0)

        # 有効期限を設定
        self._expiry.set_expiry(key, seconds)
        return Integer(1)

    async def execute_ttl(self, args: list[str]) -> Integer:
        """TTLコマンドを実行"""
        
        # 引数検証
        if len(args) != 1:
            raise CommandError("ERR wrong number of arguments for 'ttl' command")

        key = args[0]

        # Passive Expiry: 期限切れチェック
        if self._expiry.check_and_remove_expired(key):
            return Integer(-2)

        # キーが存在するかチェック
        if self._store.get(key) is None:
            return Integer(-2)

        # 有効期限を取得
        ttl = self._expiry.get_ttl(key)

        if ttl is None:
            # 有効期限が設定されていない
            return Integer(-1)

        return Integer(ttl)


class CommandError(Exception):
    """コマンド実行エラー.

    【使い方】
    コマンド実行時のエラー（引数不足、型エラー、未知のコマンド等）を表す。

    例:
        raise CommandError("ERR unknown command 'FOO'")
        raise CommandError("ERR wrong number of arguments for 'get' command")
        raise CommandError("ERR value is not an integer or out of range")
    """

    pass
