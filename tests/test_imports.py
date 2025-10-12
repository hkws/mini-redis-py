"""Test that all modules can be imported successfully."""

import pytest


def test_import_protocol() -> None:
    """Test that protocol module can be imported."""
    from mini_redis.protocol import RESPParser, RESPProtocolError

    assert RESPParser is not None
    assert RESPProtocolError is not None


def test_import_storage() -> None:
    """Test that storage module can be imported."""
    from mini_redis.storage import DataStore, StoreEntry

    assert DataStore is not None
    assert StoreEntry is not None


def test_import_expiry() -> None:
    """Test that expiry module can be imported."""
    from mini_redis.expiry import ExpiryManager

    assert ExpiryManager is not None


def test_import_commands() -> None:
    """Test that commands module can be imported."""
    from mini_redis.commands import CommandError, CommandHandler

    assert CommandHandler is not None
    assert CommandError is not None


def test_import_server() -> None:
    """Test that server module can be imported."""
    from mini_redis.server import ClientHandler, TCPServer

    assert TCPServer is not None
    assert ClientHandler is not None


def test_can_instantiate_components() -> None:
    """Test that all components can be instantiated."""
    from mini_redis.commands import CommandHandler
    from mini_redis.expiry import ExpiryManager
    from mini_redis.protocol import RESPParser
    from mini_redis.server import ClientHandler, TCPServer
    from mini_redis.storage import DataStore

    store = DataStore()
    expiry = ExpiryManager(store)
    handler = CommandHandler(store, expiry)
    parser = RESPParser()
    client_handler = ClientHandler(parser, handler)
    server = TCPServer()

    assert store is not None
    assert expiry is not None
    assert handler is not None
    assert parser is not None
    assert client_handler is not None
    assert server is not None
