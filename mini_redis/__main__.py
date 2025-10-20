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

    setup_logging()
    logger = logging.getLogger(__name__)

    # コンポーネントの初期化
    store = DataStore()
    expiry_manager = ExpiryManager(store)
    command_handler = CommandHandler(store, expiry_manager)
    parser = RESPParser()
    client_handler = ClientHandler(parser, command_handler)

    # 初期化したコンポーネントをTCPServerに注入
    server = TCPServer(
        host="127.0.0.1",
        port=6379,
        store=store,
        expiry=expiry_manager,
        client_handler=client_handler,
    )

    logger.info("Starting Mini-Redis server...")

    try:
        # サーバを起動（内部でActive Expiryも起動される）
        await server.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
    finally:
        logger.info("Shutting down Mini-Redis server...")
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
