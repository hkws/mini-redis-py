"""Unit tests for DataStore component."""

import time

import pytest

from mini_redis.storage import DataStore, StoreEntry


@pytest.fixture
def store() -> DataStore:
    """Create a fresh DataStore instance for each test."""
    return DataStore()


class TestDataStoreBasics:
    """Test basic key-value operations."""

    def test_get_nonexistent_key_returns_none(self, store: DataStore) -> None:
        """Test that getting a non-existent key returns None."""
        assert store.get("nonexistent") is None

    def test_set_and_get_key(self, store: DataStore) -> None:
        """Test setting and getting a key-value pair."""
        store.set("foo", "bar")
        assert store.get("foo") == "bar"

    def test_set_overwrites_existing_value(self, store: DataStore) -> None:
        """Test that setting an existing key overwrites its value."""
        store.set("key", "value1")
        store.set("key", "value2")
        assert store.get("key") == "value2"

    def test_delete_existing_key_returns_true(self, store: DataStore) -> None:
        """Test that deleting an existing key returns True."""
        store.set("foo", "bar")
        assert store.delete("foo") is True
        assert store.get("foo") is None

    def test_delete_nonexistent_key_returns_false(self, store: DataStore) -> None:
        """Test that deleting a non-existent key returns False."""
        assert store.delete("nonexistent") is False

    def test_exists_returns_true_for_existing_key(self, store: DataStore) -> None:
        """Test that exists returns True for an existing key."""
        store.set("foo", "bar")
        assert store.exists("foo") is True

    def test_exists_returns_false_for_nonexistent_key(self, store: DataStore) -> None:
        """Test that exists returns False for a non-existent key."""
        assert store.exists("nonexistent") is False


class TestDataStoreExpiry:
    """Test expiry management functionality."""

    def test_set_expiry_on_existing_key_returns_true(self, store: DataStore) -> None:
        """Test that setting expiry on an existing key returns True."""
        store.set("foo", "bar")
        expiry_time = time.time() + 10
        assert store.set_expiry("foo", expiry_time) is True

    def test_set_expiry_on_nonexistent_key_returns_false(self, store: DataStore) -> None:
        """Test that setting expiry on a non-existent key returns False."""
        expiry_time = time.time() + 10
        assert store.set_expiry("nonexistent", expiry_time) is False

    def test_get_expiry_returns_set_value(self, store: DataStore) -> None:
        """Test that get_expiry returns the expiry timestamp that was set."""
        store.set("foo", "bar")
        expiry_time = time.time() + 10
        store.set_expiry("foo", expiry_time)
        assert store.get_expiry("foo") == expiry_time

    def test_get_expiry_returns_none_when_not_set(self, store: DataStore) -> None:
        """Test that get_expiry returns None when expiry is not set."""
        store.set("foo", "bar")
        assert store.get_expiry("foo") is None

    def test_get_expiry_returns_none_for_nonexistent_key(self, store: DataStore) -> None:
        """Test that get_expiry returns None for a non-existent key."""
        assert store.get_expiry("nonexistent") is None

    def test_set_clears_expiry(self, store: DataStore) -> None:
        """Test that setting a new value clears the expiry."""
        store.set("foo", "bar")
        expiry_time = time.time() + 10
        store.set_expiry("foo", expiry_time)

        # Set a new value
        store.set("foo", "baz")

        # Expiry should be cleared
        assert store.get_expiry("foo") is None

    def test_get_all_keys_returns_empty_list_for_empty_store(self, store: DataStore) -> None:
        """Test that get_all_keys returns an empty list when store is empty."""
        assert store.get_all_keys() == []

    def test_get_all_keys_returns_all_keys(self, store: DataStore) -> None:
        """Test that get_all_keys returns all stored keys."""
        store.set("key1", "value1")
        store.set("key2", "value2")
        store.set("key3", "value3")

        keys = store.get_all_keys()
        assert len(keys) == 3
        assert set(keys) == {"key1", "key2", "key3"}

    def test_get_all_keys_excludes_deleted_keys(self, store: DataStore) -> None:
        """Test that get_all_keys does not include deleted keys."""
        store.set("key1", "value1")
        store.set("key2", "value2")
        store.delete("key1")

        keys = store.get_all_keys()
        assert len(keys) == 1
        assert keys == ["key2"]
