"""Mini-Redis entry point.

このモジュールは、Mini-Redisサーバのエントリポイントです。
`python -m mini_redis` で起動します。
"""

import asyncio
import logging
import sys

from mini_redis.commands import CommandHandler
from mini_redis.expiry import ExpiryManager
from mini_redis.protocol import RESPParser
from mini_redis.server import ClientHandler, TCPServer
from mini_redis.storage import DataStore


def setup_logging() -> None:
    """ログ設定を初期化."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


async def main() -> None:
    """メインエントリポイント.

    実装のヒント:
    1. 各コンポーネントのインスタンスを作成
    2. TCPServerを起動
    3. Active Expiryバックグラウンドタスクを起動
    4. Ctrl+Cで停止されるまで実行
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    # コンポーネントの初期化
    # TODO: 各コンポーネントのインスタンスを作成
    store = DataStore()
    expiry_manager = ExpiryManager(store)
    command_handler = CommandHandler(store, expiry_manager)
    parser = RESPParser()
    client_handler = ClientHandler(parser, command_handler)
    server = TCPServer()

    logger.info("Starting Mini-Redis server...")

    try:
        # TODO: サーバとActive Expiryを起動
        # ヒント: asyncio.TaskGroup()を使用して複数のタスクを管理
        raise NotImplementedError("Server startup is not implemented yet")
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
    finally:
        logger.info("Shutting down Mini-Redis server...")
        # TODO: サーバのクリーンアップ処理


if __name__ == "__main__":
    asyncio.run(main())
