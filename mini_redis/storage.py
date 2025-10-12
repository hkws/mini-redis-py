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

        実装のヒント:
        self._data辞書から取得。存在しない場合はNoneを返す
        """
        entry = self._data.get(key)
        return entry.value if entry else None

    def set(self, key: str, value: str) -> None:
        """キーに値を設定.

        Args:
            key: 設定するキー
            value: 設定する値

        Postconditions:
            - キーに値が設定される
            - 既存の有効期限はクリアされる

        実装のヒント:
        StoreEntry(value)を作成してself._dataに保存
        """
        self._data[key] = StoreEntry(value=value)

    def delete(self, key: str) -> bool:
        """キーを削除.

        Args:
            key: 削除するキー

        Returns:
            True: キーが存在して削除された
            False: キーが存在しなかった

        実装のヒント:
        dict.pop()を使用して削除。KeyErrorをキャッチしてFalseを返す
        """
        try:
            self._data.pop(key)
            return True
        except KeyError:
            return False

    def exists(self, key: str) -> bool:
        """キーが存在するかチェック.

        Args:
            key: チェックするキー

        Returns:
            キーが存在する場合はTrue、そうでない場合はFalse

        実装のヒント:
        `key in self._data`でチェック
        """
        return key in self._data

    def set_expiry(self, key: str, expiry_at: float) -> bool:
        """キーに有効期限を設定.

        Args:
            key: 有効期限を設定するキー
            expiry_at: 有効期限のUnix timestamp

        Returns:
            True: キーが存在し有効期限を設定
            False: キーが存在しない

        実装のヒント:
        キーが存在する場合、entry.expiry_atを更新
        """
        entry = self._data.get(key)
        if entry is None:
            return False
        entry.expiry_at = expiry_at
        return True

    def get_expiry(self, key: str) -> float | None:
        """キーの有効期限を取得.

        Args:
            key: 有効期限を取得するキー

        Returns:
            有効期限のUnix timestamp（設定されていない場合はNone）

        実装のヒント:
        キーが存在する場合、entry.expiry_atを返す
        """
        entry = self._data.get(key)
        return entry.expiry_at if entry else None

    def get_all_keys(self) -> list[str]:
        """すべてのキーを取得（Active expiry用）.

        Returns:
            すべてのキーのリスト

        実装のヒント:
        list(self._data.keys())を返す
        """
        return list(self._data.keys())
