"""Step 03: データストレージ層のテスト

このテストは、03-commands.mdで実装するDataStoreの基本操作を検証します。

テスト内容:
- 基本操作: get, set, delete, exists
- 有効期限管理: set_expiry, get_expiry, get_all_keys

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

    def test_exists_returns_true_for_existing_key(self, store: DataStore) -> None:
        """キーの存在確認（存在する場合）を検証.

        検証内容:
        - key in dictの動作
        - 存在する場合にTrue
        """
        store.set("foo", "bar")
        assert store.exists("foo") is True

    def test_exists_returns_false_for_nonexistent_key(self, store: DataStore) -> None:
        """キーの存在確認（存在しない場合）を検証.

        検証内容:
        - key in dictの動作
        - 存在しない場合にFalse
        """
        assert store.exists("nonexistent") is False


class TestStep03DataStoreExpiry:
    """Step 03: 有効期限管理のテスト."""

    def test_set_expiry_on_existing_key_returns_true(self, store: DataStore) -> None:
        """存在するキーに有効期限を設定することを検証.

        検証内容:
        - StoreEntry.expiry_at に Unixタイムスタンプを設定
        - 成功時にTrueを返す
        """
        store.set("foo", "bar")
        expiry_time = time.time() + 10
        assert store.set_expiry("foo", expiry_time) is True

    def test_set_expiry_on_nonexistent_key_returns_false(self, store: DataStore) -> None:
        """存在しないキーに有効期限を設定しようとした場合を検証.

        検証内容:
        - キーが存在しない場合はFalseを返す
        - エラーは発生しない
        """
        expiry_time = time.time() + 10
        assert store.set_expiry("nonexistent", expiry_time) is False

    def test_get_expiry_returns_set_value(self, store: DataStore) -> None:
        """設定された有効期限を取得することを検証.

        検証内容:
        - StoreEntry.expiry_at の読み取り
        - 設定した値と同じ値が返る
        """
        store.set("foo", "bar")
        expiry_time = time.time() + 10
        store.set_expiry("foo", expiry_time)
        assert store.get_expiry("foo") == expiry_time

    def test_get_expiry_returns_none_when_not_set(self, store: DataStore) -> None:
        """有効期限が未設定の場合にNoneを返すことを検証.

        検証内容:
        - デフォルトのexpiry_at = None
        - 有効期限未設定の場合の動作
        """
        store.set("foo", "bar")
        assert store.get_expiry("foo") is None

    def test_get_expiry_returns_none_for_nonexistent_key(self, store: DataStore) -> None:
        """存在しないキーの有効期限取得でNoneを返すことを検証."""
        assert store.get_expiry("nonexistent") is None

    def test_set_clears_expiry(self, store: DataStore) -> None:
        """set()で既存の有効期限がクリアされることを検証.

        検証内容:
        - set()で新しいStoreEntryを作成
        - 古いexpiry_atはクリアされる
        """
        store.set("foo", "bar")
        expiry_time = time.time() + 10
        store.set_expiry("foo", expiry_time)

        # 新しい値を設定
        store.set("foo", "baz")

        # 有効期限がクリアされている
        assert store.get_expiry("foo") is None

    def test_get_all_keys_returns_empty_list_for_empty_store(self, store: DataStore) -> None:
        """空のストアでget_all_keys()が空リストを返すことを検証."""
        assert store.get_all_keys() == []

    def test_get_all_keys_returns_all_keys(self, store: DataStore) -> None:
        """すべてのキーを取得することを検証.

        検証内容:
        - list(dict.keys())の動作
        - すべてのキーがリストで返る
        """
        store.set("key1", "value1")
        store.set("key2", "value2")
        store.set("key3", "value3")

        keys = store.get_all_keys()
        assert len(keys) == 3
        assert set(keys) == {"key1", "key2", "key3"}

    def test_get_all_keys_excludes_deleted_keys(self, store: DataStore) -> None:
        """削除されたキーがget_all_keys()に含まれないことを検証."""
        store.set("key1", "value1")
        store.set("key2", "value2")
        store.delete("key1")

        keys = store.get_all_keys()
        assert len(keys) == 1
        assert keys == ["key2"]
