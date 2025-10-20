"""In-memory key-value store for Mini-Redis.

このモジュールは、キー・バリューペアの保存・取得・削除、
および有効期限メタデータの管理を担当します。

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

        """
        raise NotImplementedError("get()を実装してください")

    def set(self, key: str, value: str) -> None:
        """キーに値を設定.

        Args:
            key: 設定するキー
            value: 設定する値

        Postconditions:
            - キーに値が設定される
            - 既存の有効期限はクリアされる（新しいStoreEntryを作成するため）

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

        """
        # 1. try-exceptブロックを作成
        # 2. self._data.pop(key)でキーを削除
        # 3. 成功したらTrueを返す
        # 4. KeyErrorが発生したらFalseを返す
        raise NotImplementedError("delete()を実装してください")

    def exists(self, key: str) -> bool:
        """キーが存在するかチェック.

        Args:
            key: チェックするキー

        Returns:
            キーが存在する場合はTrue、そうでない場合はFalse

        """
        raise NotImplementedError("exists()を実装してください")

    def set_expiry(self, key: str, expiry_at: float) -> bool:
        """キーに有効期限を設定.

        Args:
            key: 有効期限を設定するキー
            expiry_at: 有効期限のUnix timestamp

        Returns:
            True: キーが存在し有効期限を設定
            False: キーが存在しない
        
        """
        # 1. self._data.get(key)でエントリを取得
        # 2. エントリがNoneの場合はFalseを返す
        # 3. エントリが存在する場合、entry.expiry_atを更新
        # 4. Trueを返す
        raise NotImplementedError("set_expiry()を実装してください")

    def get_expiry(self, key: str) -> float | None:
        """キーの有効期限を取得.

        Args:
            key: 有効期限を取得するキー

        Returns:
            有効期限のUnix timestamp（設定されていない場合はNone）
        
        """
        # 1. self._data.get(key)でエントリを取得
        # 2. エントリが存在する場合、entry.expiry_atを返す
        # 3. エントリが存在しない場合、Noneを返す
        raise NotImplementedError("get_expiry()を実装してください")

    def get_all_keys(self) -> list[str]:
        """すべてのキーを取得（Active expiry用）.

        Returns:
            すべてのキーのリスト

        """
        raise NotImplementedError("get_all_keys()を実装してください")
