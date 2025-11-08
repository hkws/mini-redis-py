"""Step 03: データストレージ層のテスト

このテストは、03-commands.mdで実装するDataStoreの基本操作を検証します。

テスト内容:
- 基本操作: get, set, delete

講義資料: docs/lectures/03-commands.md (パート1: データストレージ層)
実行方法: pytest tests/step03_commands/test_storage.py -v
"""

import time

import pytest

from mini_redis.storage import DataStore, StoreEntry


@pytest.fixture
def store() -> DataStore:
    """各テストで新しいDataStoreインスタンスを作成."""
    return DataStore()


class TestStep03DataStoreBasics:
    """Step 03: データストレージの基本操作テスト."""

    def test_get_nonexistent_key_returns_none(self, store: DataStore) -> None:
        """存在しないキーに対してNoneを返すことを検証.

        検証内容:
        - dict.get(key, None)の動作
        - キーが存在しない場合の処理
        """
        assert store.get("nonexistent") is None

    def test_set_and_get_key(self, store: DataStore) -> None:
        """キーへの値の設定と取得を検証.

        検証内容:
        - StoreEntryの作成
        - dict[key] = StoreEntry(value)
        - get()で値を取得
        """
        store.set("foo", "bar")
        assert store.get("foo") == "bar"

    def test_set_overwrites_existing_value(self, store: DataStore) -> None:
        """既存のキーへの上書きを検証.

        検証内容:
        - set()で既存のエントリを完全に置き換え
        - 有効期限もクリアされる
        """
        store.set("key", "value1")
        store.set("key", "value2")
        assert store.get("key") == "value2"

    def test_delete_existing_key_returns_true(self, store: DataStore) -> None:
        """存在するキーの削除を検証.

        検証内容:
        - dict.pop(key)で削除
        - 削除成功時にTrueを返す
        - 削除後はget()でNoneが返る
        """
        store.set("foo", "bar")
        assert store.delete("foo") is True
        assert store.get("foo") is None

    def test_delete_nonexistent_key_returns_false(self, store: DataStore) -> None:
        """存在しないキーの削除を検証.

        検証内容:
        - KeyErrorをキャッチ
        - Falseを返す
        """
        assert store.delete("nonexistent") is False

