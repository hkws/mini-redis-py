"""Command handler for Mini-Redis.

このモジュールは、Redisコマンドのルーティングと実行、
およびPassive expiryの統合を担当します。
"""

import time

from mini_redis.expiry import ExpiryManager
from mini_redis.storage import DataStore

CommandResult = str | int | None


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

    def __init__(self, store: DataStore, expiry: ExpiryManager) -> None:
        """ハンドラを初期化.

        Args:
            store: データストアのインスタンス
            expiry: 有効期限マネージャのインスタンス
        """
        self._store = store
        self._expiry = expiry

    async def execute(self, command: list[str]) -> CommandResult:
        """コマンドを実行.

        Args:
            command: コマンド名と引数のリスト

        Returns:
            コマンドの実行結果

        Raises:
            CommandError: コマンド実行エラー

        実装のヒント:
        1. command[0]をコマンド名として取得（大文字変換）
        2. コマンド名に応じてexecute_*メソッドを呼び出す
        3. 未知のコマンドの場合はCommandErrorをraise
        """
        if not command:
            raise CommandError("ERR empty command")

        # 1. コマンド名を取得（大文字変換）
        cmd_name = command[0].upper()
        args = command[1:]

        # 2. コマンド名に応じてルーティング
        if cmd_name == "PING":
            if len(args) != 0:
                raise CommandError("ERR wrong number of arguments for 'ping' command")
            return await self.execute_ping()

        elif cmd_name == "GET":
            if len(args) != 1:
                raise CommandError("ERR wrong number of arguments for 'get' command")
            return await self.execute_get(args[0])

        elif cmd_name == "SET":
            if len(args) != 2:
                raise CommandError("ERR wrong number of arguments for 'set' command")
            return await self.execute_set(args[0], args[1])

        elif cmd_name == "INCR":
            if len(args) != 1:
                raise CommandError("ERR wrong number of arguments for 'incr' command")
            return await self.execute_incr(args[0])

        elif cmd_name == "EXPIRE":
            if len(args) != 2:
                raise CommandError("ERR wrong number of arguments for 'expire' command")
            try:
                seconds = int(args[1])
            except ValueError as e:
                raise CommandError("ERR value is not an integer or out of range") from e
            return await self.execute_expire(args[0], seconds)

        elif cmd_name == "TTL":
            if len(args) != 1:
                raise CommandError("ERR wrong number of arguments for 'ttl' command")
            return await self.execute_ttl(args[0])

        else:
            # 3. 未知のコマンド
            raise CommandError(f"ERR unknown command '{cmd_name}'")

    async def execute_ping(self) -> str:
        """PING: 常に'PONG'を返す.

        Returns:
            "PONG"

        実装のヒント:
        単純に "PONG" を返すだけ
        """
        return "PONG"

    async def execute_get(self, key: str) -> str | None:
        """GET: キーの値を取得.

        Args:
            key: 取得するキー

        Returns:
            キーが存在する場合は値、存在しない場合はNone

        実装のヒント:
        1. self._expiry.check_and_remove_expired(key)を呼び出す（Passive expiry）
        2. self._store.get(key)でキーの値を取得
        3. 結果を返す
        """
        # 1. Passive expiryチェック
        self._expiry.check_and_remove_expired(key)
        # 2. キーの値を取得
        return self._store.get(key)

    async def execute_set(self, key: str, value: str) -> str:
        """SET: キーに値を設定.

        Args:
            key: 設定するキー
            value: 設定する値

        Returns:
            "OK"

        実装のヒント:
        1. self._store.set(key, value)でキーに値を設定
        2. "OK"を返す
        """
        self._store.set(key, value)
        return "OK"

    async def execute_incr(self, key: str) -> int:
        """INCR: キーの値を1増加.

        Args:
            key: 増加させるキー

        Returns:
            増加後の値

        Raises:
            CommandError: 値が整数でない場合

        実装のヒント:
        1. self._expiry.check_and_remove_expired(key)を呼び出す（Passive expiry）
        2. self._store.get(key)で現在の値を取得
        3. 値が存在しない場合は1を設定して返す
        4. 値が整数でない場合はCommandErrorをraise
        5. 値を+1してself._store.set(key, new_value)で保存
        6. 新しい値を返す
        """
        # 1. Passive expiryチェック
        self._expiry.check_and_remove_expired(key)

        # 2. 現在の値を取得
        current_value = self._store.get(key)

        # 3. 値が存在しない場合は1を設定
        if current_value is None:
            self._store.set(key, "1")
            return 1

        # 4. 値が整数でない場合はエラー
        try:
            int_value = int(current_value)
        except ValueError as e:
            raise CommandError("ERR value is not an integer or out of range") from e

        # 5. 値を+1して保存
        new_value = int_value + 1
        self._store.set(key, str(new_value))

        # 6. 新しい値を返す
        return new_value

    async def execute_expire(self, key: str, seconds: int) -> int:
        """EXPIRE: キーに有効期限を設定.

        Args:
            key: 有効期限を設定するキー
            seconds: 有効期限の秒数

        Returns:
            1: キーが存在し有効期限を設定
            0: キーが存在しない

        実装のヒント:
        1. self._expiry.check_and_remove_expired(key)を呼び出す（Passive expiry）
        2. キーが存在するか確認
        3. 存在しない場合は0を返す
        4. 存在する場合は有効期限を設定して1を返す
           - expiry_at = time.time() + seconds
           - self._store.set_expiry(key, expiry_at)
        """
        # 1. Passive expiryチェック
        self._expiry.check_and_remove_expired(key)

        # 2. キーが存在するか確認
        if not self._store.exists(key):
            return 0

        # 4. 有効期限を設定
        expiry_at = time.time() + seconds
        self._store.set_expiry(key, expiry_at)
        return 1

    async def execute_ttl(self, key: str) -> int:
        """TTL: キーの残り有効秒数を取得.

        Args:
            key: 有効期限を取得するキー

        Returns:
            残り秒数（正の整数）
            -1: キーは存在するが有効期限なし
            -2: キーが存在しない

        実装のヒント:
        1. self._expiry.check_and_remove_expired(key)を呼び出す（Passive expiry）
        2. キーが存在しない場合は-2を返す
        3. 有効期限が設定されていない場合は-1を返す
        4. 有効期限が設定されている場合は残り秒数を計算して返す
           - remaining = int(expiry_at - time.time())
           - return max(0, remaining)
        """
        # 1. Passive expiryチェック
        self._expiry.check_and_remove_expired(key)

        # 2. キーが存在しない場合は-2を返す
        if not self._store.exists(key):
            return -2

        # 3. 有効期限が設定されていない場合は-1を返す
        expiry_at = self._store.get_expiry(key)
        if expiry_at is None:
            return -1

        # 4. 残り秒数を計算して返す
        remaining = int(expiry_at - time.time())
        return max(0, remaining)


class CommandError(Exception):
    """コマンド実行エラー."""

    pass
