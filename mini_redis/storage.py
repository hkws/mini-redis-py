"""In-memory key-value store for Mini-Redis.

このモジュールは、キー・バリューペアの保存・取得・削除、
および有効期限メタデータの管理を担当します。

【実装順序のガイド】
1. get() - シンプルな辞書操作から始める
2. set() - StoreEntryを作成して保存
3. exists() - 辞書のキー存在確認
4. delete() - KeyErrorのハンドリングに注意
5. set_expiry() - エントリが存在する場合のみ設定
6. get_expiry() - エントリの有効期限を取得
7. get_all_keys() - Active expiry用
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StoreEntry:
    """ストレージのエントリ.

    Attributes:
        value: 保存される文字列値
        expiry_at: 有効期限のUnix timestamp（Noneの場合は期限なし）

    【使い方】
    entry = StoreEntry(value="hello", expiry_at=1234567890.0)
    entry = StoreEntry(value="world")  # expiry_atはNone
    """

    value: str
    expiry_at: float | None = field(default=None)


class DataStore:
    """インメモリのキー・バリューストア.

    責務:
    - キー・バリューペアの保存・取得・削除
    - 有効期限メタデータの管理

    実装のヒント:
    1. 内部データ構造として Dict[str, StoreEntry] を使用
    2. 各メソッドは辞書操作を薄くラップするだけでOK
    3. 有効期限のチェックは呼び出し側（ExpiryManager）の責任
    """

    def __init__(self) -> None:
        """ストアを初期化."""
        self._data: dict[str, StoreEntry] = {}

    def get(self, key: str) -> str | None:
        """キーの値を取得.

        Args:
            key: 取得するキー

        Returns:
            値が存在する場合はその値、存在しない場合はNone

        【実装ステップ】
        1. self._data.get(key)でエントリを取得
        2. エントリが存在する場合はentry.valueを返す
        3. エントリが存在しない場合はNoneを返す

        【ヒント】
        三項演算子を使うと簡潔:
        return entry.value if entry else None

        【よくある間違い】
        ❌ self._data[key]を使う → KeyErrorが発生する
        ✅ self._data.get(key)を使う → Noneを返す
        """
        # TODO: 実装してください
        raise NotImplementedError("get()を実装してください")

    def set(self, key: str, value: str) -> None:
        """キーに値を設定.

        Args:
            key: 設定するキー
            value: 設定する値

        Postconditions:
            - キーに値が設定される
            - 既存の有効期限はクリアされる（新しいStoreEntryを作成するため）

        【実装ステップ】
        1. StoreEntry(value=value)を作成
        2. self._data[key]に保存

        【ヒント】
        1行で書ける: self._data[key] = StoreEntry(value=value)

        【注意】
        既存のエントリがある場合、上書きされる（有効期限もクリアされる）
        """
        # TODO: 実装してください
        raise NotImplementedError("set()を実装してください")

    def delete(self, key: str) -> bool:
        """キーを削除.

        Args:
            key: 削除するキー

        Returns:
            True: キーが存在して削除された
            False: キーが存在しなかった

        【実装ステップ】
        1. try-exceptブロックを作成
        2. self._data.pop(key)でキーを削除
        3. 成功したらTrueを返す
        4. KeyErrorが発生したらFalseを返す

        【ヒント】
        pop()は要素を削除して値を返す。存在しない場合はKeyErrorをraise

        【よくある間違い】
        ❌ del self._data[key]を使う → 戻り値の制御が難しい
        ✅ self._data.pop(key)を使う → 例外ハンドリングで戻り値を制御
        """
        # TODO: 実装してください
        # try:
        #     self._data.pop(key)
        #     return True
        # except KeyError:
        #     return False
        raise NotImplementedError("delete()を実装してください")

    def exists(self, key: str) -> bool:
        """キーが存在するかチェック.

        Args:
            key: チェックするキー

        Returns:
            キーが存在する場合はTrue、そうでない場合はFalse

        【実装ステップ】
        1. `key in self._data`でチェック

        【ヒント】
        最もシンプルなメソッド。1行で実装できる。

        例:
        >>> store = DataStore()
        >>> store.set("foo", "bar")
        >>> store.exists("foo")
        True
        >>> store.exists("baz")
        False
        """
        # TODO: 実装してください
        raise NotImplementedError("exists()を実装してください")

    def set_expiry(self, key: str, expiry_at: float) -> bool:
        """キーに有効期限を設定.

        Args:
            key: 有効期限を設定するキー
            expiry_at: 有効期限のUnix timestamp

        Returns:
            True: キーが存在し有効期限を設定
            False: キーが存在しない

        【実装ステップ】
        1. self._data.get(key)でエントリを取得
        2. エントリがNoneの場合はFalseを返す
        3. エントリが存在する場合、entry.expiry_atを更新
        4. Trueを返す

        【ヒント】
        エントリが存在しない場合は何もせずFalseを返す
        エントリが存在する場合はexpiry_atを更新してTrueを返す

        例:
        >>> store = DataStore()
        >>> store.set("foo", "bar")
        >>> store.set_expiry("foo", 1234567890.0)
        True
        >>> store.set_expiry("baz", 1234567890.0)
        False
        """
        # TODO: 実装してください
        # 1. entry = self._data.get(key)
        # 2. if entry is None: return False
        # 3. entry.expiry_at = expiry_at
        # 4. return True
        raise NotImplementedError("set_expiry()を実装してください")

    def get_expiry(self, key: str) -> float | None:
        """キーの有効期限を取得.

        Args:
            key: 有効期限を取得するキー

        Returns:
            有効期限のUnix timestamp（設定されていない場合はNone）

        【実装ステップ】
        1. self._data.get(key)でエントリを取得
        2. エントリが存在する場合、entry.expiry_atを返す
        3. エントリが存在しない場合、Noneを返す

        【ヒント】
        三項演算子を使うと簡潔:
        return entry.expiry_at if entry else None

        例:
        >>> store = DataStore()
        >>> store.set("foo", "bar")
        >>> store.get_expiry("foo")
        None
        >>> store.set_expiry("foo", 1234567890.0)
        True
        >>> store.get_expiry("foo")
        1234567890.0
        """
        # TODO: 実装してください
        raise NotImplementedError("get_expiry()を実装してください")

    def get_all_keys(self) -> list[str]:
        """すべてのキーを取得（Active expiry用）.

        Returns:
            すべてのキーのリスト

        【実装ステップ】
        1. list(self._data.keys())を返す

        【ヒント】
        最もシンプルなメソッドの1つ。1行で実装できる。

        【注意】
        Active expiryで使用するため、すべてのキーのスナップショットが必要。
        dict.keys()だけだとビュー（参照）なので、list()で実体化する。

        例:
        >>> store = DataStore()
        >>> store.set("foo", "bar")
        >>> store.set("baz", "qux")
        >>> store.get_all_keys()
        ['foo', 'baz']
        """
        # TODO: 実装してください
        raise NotImplementedError("get_all_keys()を実装してください")
