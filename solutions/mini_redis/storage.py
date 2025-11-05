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
    entry = StoreEntry(value="hello", expiry_at=1234567890)
    entry = StoreEntry(value="world")  # expiry_atはNone
    """

    value: str
    expiry_at: int | None = field(default=None)


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
        entry = self._data.get(key)
        return entry.value if entry else None

    def set(self, key: str, value: str) -> None:
        self._data[key] = StoreEntry(value=value)

    def delete(self, key: str) -> bool:
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

        """
        return key in self._data

    def set_expiry(self, key: str, expiry_at: int) -> None:
        """キーに有効期限を設定する"""
        entry = self._data.get(key)
        if entry:
            entry.expiry_at = expiry_at

    def get_expiry(self, key: str) -> int | None:
        """キーの有効期限を取得する"""
        entry = self._data.get(key)
        return entry.expiry_at if entry else None

    def get_all_keys(self) -> list[str]:
        """全てのキー一覧を取得する"""
        return list(self._data.keys())

    def get_keys_with_expiry(self) -> list[str]:
        """有効期限が設定されたキーの一覧を取得.

        Returns:
            有効期限が設定されたキーのリスト

        """
        raise NotImplementedError("get_keys_with_expiry()を実装してください")
