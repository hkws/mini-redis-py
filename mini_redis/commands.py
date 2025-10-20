"""Command handler for Mini-Redis.

このモジュールは、Redisコマンドのルーティングと実行、
およびPassive expiryの統合を担当します。

"""

import time

# NOTE: ExpiryManagerとDataStoreは別ファイルで定義されています
# from mini_redis.expiry import ExpiryManager
# from mini_redis.storage import DataStore

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

    def __init__(self, store, expiry) -> None:
        """ハンドラを初期化.

        Args:
            store: DataStoreのインスタンス
            expiry: ExpiryManagerのインスタンス

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
        """
        # 1. 空コマンドのチェック
        #    commandが空の場合、CommandError("ERR empty command"

        # 2  コマンド名と引数の取得
        # 2.1 command[0]をコマンド名として取得
        # 2.2 .upper()で大文字に変換（PINGもpingも同じ扱い）
        # 2.3 command[1:]を引数リストとして取得

        # 3 コマンドのルーティング
        # 1. PING:
        #    - 引数が0個であることを確認（でなければCommandError）
        #    - execute_ping()を呼び出す

        # 2. GET:
        #    - 引数が1個であることを確認（でなければCommandError）
        #    - execute_get(args[0])を呼び出す

        # 3. SET:
        #    - 引数が2個であることを確認（でなければCommandError）
        #    - execute_set(args[0], args[1])を呼び出す

        # 4. INCR:
        #    - 引数が1個であることを確認（でなければCommandError）
        #    - execute_incr(args[0])を呼び出す

        # 5. EXPIRE:
        #    - 引数が2個であることを確認（でなければCommandError）
        #    - args[1]をint()で整数に変換（ValueErrorの場合はCommandError）
        #    - execute_expire(args[0], seconds)を呼び出す

        # 6. TTL:
        #    - 引数が1個であることを確認（でなければCommandError）
        #    - execute_ttl(args[0])を呼び出す

        # 7. その他:
        #    - CommandError(f"ERR unknown command '{cmd_name}'")をraise

        raise NotImplementedError("execute()を実装してください")

    async def execute_ping(self) -> str:
        """PING: 常に'PONG'を返す.

        Returns:
            "PONG"

        """
        raise NotImplementedError("execute_ping()を実装してください")

    async def execute_get(self, key: str) -> str | None:
        """GET: キーの値を取得.

        Args:
            key: 取得するキー

        Returns:
            キーが存在する場合は値、存在しない場合はNone

        """
        # 1. self._expiry.check_and_remove_expired(key)を呼び出す（Passive expiry）
        # 2. self._store.get(key)でキーの値を取得し返却
        raise NotImplementedError("execute_get()を実装してください")

    async def execute_set(self, key: str, value: str) -> str:
        """SET: キーに値を設定.

        Args:
            key: 設定するキー
            value: 設定する値

        Returns:
            "OK"

        【実装ステップ】
        1. self._store.set(key, value)でキーに値を設定
        2. "OK"を返す

        【注意】
        SETコマンドは既存の有効期限をクリアする。
        store.set()が新しいStoreEntryを作成するため、自動的にクリアされる。

        例:
        >>> handler.execute_set("mykey", "hello")
        "OK"
        """
        # 1. self._store.set(key, value)でキーに値を設定
        # 2. "OK"を返す
        raise NotImplementedError("execute_set()を実装してください")

    async def execute_incr(self, key: str) -> int:
        """INCR: キーの値を1増加.

        Args:
            key: 増加させるキー

        Returns:
            増加後の値

        Raises:
            CommandError: 値が整数でない場合

        """
        # 1. Passive expiryチェック
        # 2. Storeから現在の値を取得
        # 3. キーが存在しない場合は1を設定
        # 4. 値を整数に変換
        # 5. 値をインクリメントして保存

        raise NotImplementedError("execute_incr()を実装してください")

    async def execute_expire(self, key: str, seconds: int) -> int:
        """EXPIRE: キーに有効期限を設定.

        Args:
            key: 有効期限を設定するキー
            seconds: 有効期限の秒数

        Returns:
            1: キーが存在し有効期限を設定
            0: キーが存在しない

        """
        # 1. Passive expiryチェック
        # 2. キーの存在確認
        # 3. 有効期限を設定
        raise NotImplementedError("execute_expire()を実装してください")

    async def execute_ttl(self, key: str) -> int:
        """TTL: キーの残り有効秒数を取得.

        Args:
            key: 有効期限を取得するキー

        Returns:
            残り秒数（正の整数）
            -1: キーは存在するが有効期限なし
            -2: キーが存在しない

        【実装ステップ】
        ステップ1: Passive expiryチェック
        ───────────────────────────
        1. self._expiry.check_and_remove_expired(key)を呼び出す

        ステップ2: キーの存在確認
        ─────────────────────
        1. self._store.exists(key)でキーが存在するか確認
        2. 存在しない場合は-2を返す

        ステップ3: 有効期限の確認
        ─────────────────────
        1. self._store.get_expiry(key)で有効期限を取得
        2. expiry_atがNoneの場合は-1を返す

        ステップ4: 残り秒数を計算
        ─────────────────────
        1. remaining = int(expiry_at - time.time())で残り秒数を計算
        2. max(0, remaining)で負の値を0にする
        3. 結果を返す

        【注意】
        残り秒数が負の値になることがある（Active expiryで削除される前）。
        その場合は0を返す。

        例:
        >>> handler.execute_ttl("mykey")
        9  # 9秒後に期限切れ
        >>> handler.execute_ttl("permanent")
        -1  # 有効期限なし
        >>> handler.execute_ttl("nonexistent")
        -2  # キーが存在しない
        """
        # 1. Passive expiryチェック
        # 2. キーの存在確認
        # 3. 有効期限の確認
        # 4. 残り秒数を計算
        #    残り秒数が負の場合は0にすること
        raise NotImplementedError("execute_ttl()を実装してください")


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
