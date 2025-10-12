"""Command handler for Mini-Redis.

このモジュールは、Redisコマンドのルーティングと実行、
およびPassive expiryの統合を担当します。

【実装順序のガイド】
1. execute_ping() - 最もシンプルなコマンド
2. execute_set() - 基本的な書き込みコマンド
3. execute_get() - Passive expiryを含む読み込みコマンド
4. execute_incr() - 型チェックと変換が必要
5. execute_expire() - 有効期限の設定
6. execute_ttl() - 有効期限の取得
7. execute() - すべてのコマンドをルーティング
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

        【実装ステップ】
        1. self._store = store
        2. self._expiry = expiry
        """
        # TODO: 実装してください
        raise NotImplementedError("__init__()を実装してください")

    async def execute(self, command: list[str]) -> CommandResult:
        """コマンドを実行.

        Args:
            command: コマンド名と引数のリスト

        Returns:
            コマンドの実行結果

        Raises:
            CommandError: コマンド実行エラー

        【実装ステップ】
        ステップ1: 空コマンドのチェック
        ─────────────────────────
        1. commandが空の場合、CommandError("ERR empty command")をraise

        ステップ2: コマンド名と引数の取得
        ────────────────────────────
        1. command[0]をコマンド名として取得
        2. .upper()で大文字に変換（PINGもpingも同じ扱い）
        3. command[1:]を引数リストとして取得

        ステップ3: コマンドのルーティング
        ──────────────────────────
        if-elif-elseで各コマンドにルーティング:

        1. PING:
           - 引数が0個であることを確認（でなければCommandError）
           - execute_ping()を呼び出す

        2. GET:
           - 引数が1個であることを確認（でなければCommandError）
           - execute_get(args[0])を呼び出す

        3. SET:
           - 引数が2個であることを確認（でなければCommandError）
           - execute_set(args[0], args[1])を呼び出す

        4. INCR:
           - 引数が1個であることを確認（でなければCommandError）
           - execute_incr(args[0])を呼び出す

        5. EXPIRE:
           - 引数が2個であることを確認（でなければCommandError）
           - args[1]をint()で整数に変換（ValueErrorの場合はCommandError）
           - execute_expire(args[0], seconds)を呼び出す

        6. TTL:
           - 引数が1個であることを確認（でなければCommandError）
           - execute_ttl(args[0])を呼び出す

        7. その他:
           - CommandError(f"ERR unknown command '{cmd_name}'")をraise

        【よくある間違い】
        ❌ コマンド名の大文字変換を忘れる → pingとPINGが別コマンドになる
        ❌ 引数の数チェックを忘れる → IndexErrorが発生する
        ❌ EXPIREの引数をint変換し忘れる → 型エラー

        【ヒント】
        引数チェックのエラーメッセージ:
        "ERR wrong number of arguments for 'ping' command"
        """
        # TODO: ステップ1を実装してください
        # if not command:
        #     raise CommandError("ERR empty command")

        # TODO: ステップ2を実装してください
        # cmd_name = command[0].upper()
        # args = command[1:]

        # TODO: ステップ3を実装してください
        # if cmd_name == "PING":
        #     ...
        # elif cmd_name == "GET":
        #     ...
        # ... (他のコマンド)
        # else:
        #     raise CommandError(f"ERR unknown command '{cmd_name}'")

        raise NotImplementedError("execute()を実装してください")

    async def execute_ping(self) -> str:
        """PING: 常に'PONG'を返す.

        Returns:
            "PONG"

        【実装ステップ】
        1. "PONG"を返す

        【ヒント】
        最もシンプルなコマンド。1行で実装できる。
        """
        # TODO: 実装してください
        raise NotImplementedError("execute_ping()を実装してください")

    async def execute_get(self, key: str) -> str | None:
        """GET: キーの値を取得.

        Args:
            key: 取得するキー

        Returns:
            キーが存在する場合は値、存在しない場合はNone

        【実装ステップ】
        1. self._expiry.check_and_remove_expired(key)を呼び出す（Passive expiry）
        2. self._store.get(key)でキーの値を取得
        3. 結果を返す

        【重要】
        Passive expiryを必ず最初に呼び出すこと！
        これにより、期限切れキーがアクセス時に削除される。

        例:
        >>> # 期限切れキーの場合
        >>> handler.execute_get("expired_key")
        None  # check_and_remove_expired()で削除されたため
        """
        # TODO: 実装してください
        # 1. self._expiry.check_and_remove_expired(key)
        # 2. return self._store.get(key)
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
        # TODO: 実装してください
        raise NotImplementedError("execute_set()を実装してください")

    async def execute_incr(self, key: str) -> int:
        """INCR: キーの値を1増加.

        Args:
            key: 増加させるキー

        Returns:
            増加後の値

        Raises:
            CommandError: 値が整数でない場合

        【実装ステップ】
        ステップ1: Passive expiryチェック
        ───────────────────────────
        1. self._expiry.check_and_remove_expired(key)を呼び出す

        ステップ2: 現在の値を取得
        ─────────────────────
        1. self._store.get(key)で現在の値を取得

        ステップ3: キーが存在しない場合の処理
        ──────────────────────────────
        1. current_valueがNoneの場合:
           - self._store.set(key, "1")で1を設定
           - 1を返す

        ステップ4: 値を整数に変換
        ────────────────────
        1. try-exceptブロックを作成
        2. int(current_value)で整数に変換
        3. ValueErrorが発生した場合:
           - CommandError("ERR value is not an integer or out of range")をraise

        ステップ5: 値を増加して保存
        ──────────────────────
        1. new_value = int_value + 1
        2. self._store.set(key, str(new_value))で保存
        3. new_valueを返す

        【よくある間違い】
        ❌ 整数のまま保存する → ストアは文字列のみ対応
        ✅ str(new_value)で文字列に変換して保存

        例:
        >>> handler.execute_incr("counter")
        1  # キーが存在しない場合
        >>> handler.execute_incr("counter")
        2
        >>> handler.execute_incr("counter")
        3
        """
        # TODO: ステップ1を実装してください
        # self._expiry.check_and_remove_expired(key)

        # TODO: ステップ2を実装してください
        # current_value = self._store.get(key)

        # TODO: ステップ3を実装してください
        # if current_value is None:
        #     self._store.set(key, "1")
        #     return 1

        # TODO: ステップ4を実装してください
        # try:
        #     int_value = int(current_value)
        # except ValueError as e:
        #     raise CommandError("ERR value is not an integer or out of range") from e

        # TODO: ステップ5を実装してください
        # new_value = int_value + 1
        # self._store.set(key, str(new_value))
        # return new_value

        raise NotImplementedError("execute_incr()を実装してください")

    async def execute_expire(self, key: str, seconds: int) -> int:
        """EXPIRE: キーに有効期限を設定.

        Args:
            key: 有効期限を設定するキー
            seconds: 有効期限の秒数

        Returns:
            1: キーが存在し有効期限を設定
            0: キーが存在しない

        【実装ステップ】
        ステップ1: Passive expiryチェック
        ───────────────────────────
        1. self._expiry.check_and_remove_expired(key)を呼び出す

        ステップ2: キーの存在確認
        ─────────────────────
        1. self._store.exists(key)でキーが存在するか確認
        2. 存在しない場合は0を返す

        ステップ3: 有効期限を設定
        ─────────────────────
        1. expiry_at = time.time() + secondsで有効期限を計算
        2. self._store.set_expiry(key, expiry_at)で有効期限を設定
        3. 1を返す

        【ヒント】
        time.time()は現在時刻のUnix timestamp（浮動小数点）を返す

        例:
        >>> handler.execute_expire("mykey", 10)
        1  # 10秒後に期限切れ
        >>> handler.execute_expire("nonexistent", 10)
        0  # キーが存在しない
        """
        # TODO: ステップ1を実装してください
        # self._expiry.check_and_remove_expired(key)

        # TODO: ステップ2を実装してください
        # if not self._store.exists(key):
        #     return 0

        # TODO: ステップ3を実装してください
        # expiry_at = time.time() + seconds
        # self._store.set_expiry(key, expiry_at)
        # return 1

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
        # TODO: ステップ1を実装してください
        # self._expiry.check_and_remove_expired(key)

        # TODO: ステップ2を実装してください
        # if not self._store.exists(key):
        #     return -2

        # TODO: ステップ3を実装してください
        # expiry_at = self._store.get_expiry(key)
        # if expiry_at is None:
        #     return -1

        # TODO: ステップ4を実装してください
        # remaining = int(expiry_at - time.time())
        # return max(0, remaining)

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
