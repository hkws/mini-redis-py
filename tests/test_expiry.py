"""Tests for ExpiryManager."""

import time

import pytest

from mini_redis.expiry import ExpiryManager
from mini_redis.storage import DataStore


class TestPassiveExpiry:
    """Passive expiryのテスト."""

    def test_check_and_remove_expired_returns_false_for_nonexistent_key(self) -> None:
        """存在しないキーに対してFalseを返す."""
        store = DataStore()
        expiry = ExpiryManager(store)

        result = expiry.check_and_remove_expired("nonexistent")

        assert result is False

    def test_check_and_remove_expired_returns_false_for_key_without_expiry(self) -> None:
        """有効期限が設定されていないキーに対してFalseを返す."""
        store = DataStore()
        expiry = ExpiryManager(store)
        store.set("key1", "value1")

        result = expiry.check_and_remove_expired("key1")

        assert result is False
        assert store.exists("key1") is True

    def test_check_and_remove_expired_returns_false_for_valid_key(self) -> None:
        """有効期限内のキーに対してFalseを返す."""
        store = DataStore()
        expiry = ExpiryManager(store)
        store.set("key1", "value1")
        # 10秒後に期限切れ
        store.set_expiry("key1", time.time() + 10)

        result = expiry.check_and_remove_expired("key1")

        assert result is False
        assert store.exists("key1") is True

    def test_check_and_remove_expired_removes_expired_key(self) -> None:
        """期限切れのキーを削除してTrueを返す."""
        store = DataStore()
        expiry = ExpiryManager(store)
        store.set("key1", "value1")
        # 過去の時刻を設定（既に期限切れ）
        store.set_expiry("key1", time.time() - 1)

        result = expiry.check_and_remove_expired("key1")

        assert result is True
        assert store.exists("key1") is False

    def test_check_and_remove_expired_at_exact_expiry_time(self) -> None:
        """有効期限ちょうどのキーは期限切れとして削除される."""
        store = DataStore()
        expiry = ExpiryManager(store)
        store.set("key1", "value1")
        # 現在時刻を有効期限に設定
        expiry_time = time.time()
        store.set_expiry("key1", expiry_time)

        # わずかに時間を進める
        time.sleep(0.01)
        result = expiry.check_and_remove_expired("key1")

        assert result is True
        assert store.exists("key1") is False
