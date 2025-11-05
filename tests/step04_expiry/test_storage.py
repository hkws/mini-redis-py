"""Step 04: ストレージ層の有効期限管理メソッドのテスト

このテストは、04-expiry.mdで実装する有効期限管理メソッドを検証します。

テスト内容:
- set_expiry(): 有効期限の設定
- get_expiry(): 有効期限の取得
- get_keys_with_expiry(): 有効期限付きキー一覧の取得

講義資料: docs/lectures/04-expiry.md (パート0: ストレージ層への有効期限メソッド追加)
実行方法: pytest tests/step04_expiry/test_storage.py -v
"""

import time

import pytest

from mini_redis.storage import DataStore


@pytest.fixture
def store() -> DataStore:
    """各テストで新しいDataStoreインスタンスを作成."""
    return DataStore()


class TestStep04StorageExpiry:
    """Step 04: ストレージ層の有効期限管理メソッドのテスト."""

    def test_set_expiry_on_existing_key(self, store: DataStore) -> None:
        """存在するキーに有効期限を設定することを検証.

        検証内容:
        - StoreEntry.expiry_at に Unixタイムスタンプを設定
        - entry.expiry_at が更新される
        """
        store.set("foo", "bar")
        expiry_time = int(time.time()) + 10

        store.set_expiry("foo", expiry_time)

        assert store.get_expiry("foo") == expiry_time

    def test_set_expiry_on_nonexistent_key_does_nothing(self, store: DataStore) -> None:
        """存在しないキーに有効期限を設定しようとした場合を検証.

        検証内容:
        - キーが存在しない場合は何もしない
        - エラーは発生しない
        """
        expiry_time = int(time.time()) + 10

        # 存在しないキーに設定を試みる（エラーにならない）
        store.set_expiry("nonexistent", expiry_time)

        # 有効期限は設定されない（キーが存在しないため）
        assert store.get_expiry("nonexistent") is None

    def test_get_expiry_returns_set_value(self, store: DataStore) -> None:
        """設定された有効期限を取得することを検証.

        検証内容:
        - StoreEntry.expiry_at の読み取り
        - 設定した値と同じ値が返る
        """
        store.set("foo", "bar")
        expiry_time = int(time.time()) + 10
        store.set_expiry("foo", expiry_time)

        result = store.get_expiry("foo")

        assert result == expiry_time

    def test_get_expiry_returns_none_when_not_set(self, store: DataStore) -> None:
        """有効期限が未設定の場合にNoneを返すことを検証.

        検証内容:
        - デフォルトのexpiry_at = None
        - 有効期限未設定の場合の動作
        """
        store.set("foo", "bar")

        result = store.get_expiry("foo")

        assert result is None

    def test_get_expiry_returns_none_for_nonexistent_key(self, store: DataStore) -> None:
        """存在しないキーの有効期限取得でNoneを返すことを検証."""
        result = store.get_expiry("nonexistent")

        assert result is None

    def test_set_clears_expiry(self, store: DataStore) -> None:
        """set()で既存の有効期限がクリアされることを検証.

        検証内容:
        - set()で新しいStoreEntryを作成
        - 古いexpiry_atはクリアされる
        """
        store.set("foo", "bar")
        expiry_time = int(time.time()) + 10
        store.set_expiry("foo", expiry_time)

        # 新しい値を設定
        store.set("foo", "baz")

        # 有効期限がクリアされている
        assert store.get_expiry("foo") is None

    def test_set_expiry_updates_existing_expiry(self, store: DataStore) -> None:
        """既存の有効期限を更新できることを検証.

        検証内容:
        - set_expiry()を複数回呼び出す
        - 最後に設定した値が有効になる
        """
        store.set("foo", "bar")

        # 最初の有効期限を設定
        first_expiry = int(time.time()) + 10
        store.set_expiry("foo", first_expiry)
        assert store.get_expiry("foo") == first_expiry

        # 有効期限を更新
        second_expiry = int(time.time()) + 20
        store.set_expiry("foo", second_expiry)
        assert store.get_expiry("foo") == second_expiry

    def test_get_all_keys_returns_empty_list_for_empty_store(
        self, store: DataStore
    ) -> None:
        """空のストアで空のリストを返すことを検証.

        検証内容:
        - データが何も保存されていない場合
        - 空のリストが返る
        """
        result = store.get_all_keys()

        assert result == []

    def test_get_all_keys_returns_all_keys(self, store: DataStore) -> None:
        """すべてのキーを取得することを検証.

        検証内容:
        - 複数のキーを設定
        - すべてのキーが含まれるリストが返る
        """
        store.set("key1", "value1")
        store.set("key2", "value2")
        store.set("key3", "value3")

        result = store.get_all_keys()

        assert set(result) == {"key1", "key2", "key3"}

    def test_get_all_keys_includes_keys_with_and_without_expiry(
        self, store: DataStore
    ) -> None:
        """有効期限の有無に関わらずすべてのキーを取得することを検証.

        検証内容:
        - 有効期限付きキーと無期限キーを混在させる
        - すべてのキーが取得される
        """
        store.set("no_expiry", "value1")
        store.set("with_expiry", "value2")
        expiry_time = int(time.time()) + 10
        store.set_expiry("with_expiry", expiry_time)

        result = store.get_all_keys()

        assert set(result) == {"no_expiry", "with_expiry"}

    def test_get_all_keys_reflects_deletions(self, store: DataStore) -> None:
        """削除されたキーが一覧に含まれないことを検証.

        検証内容:
        - キーを設定後に削除
        - 削除されたキーは一覧に含まれない
        """
        store.set("key1", "value1")
        store.set("key2", "value2")
        store.delete("key1")

        result = store.get_all_keys()

        assert result == ["key2"]
