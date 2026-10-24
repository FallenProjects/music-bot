# Copyright (c) 2025 AshokShau
# Licensed under the GNU AGPL v3.0: https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import signal

from src import client


async def run_bot() -> None:
    """Run startup and idle on one loop, cleaning up even after partial startup."""
    loop = asyncio.get_running_loop()
    task = asyncio.current_task()
    assert task is not None
    registered: list[signal.Signals] = []
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, task.cancel)
            registered.append(sig)
        except NotImplementedError:
            # asyncio.run handles Ctrl-C on platforms without loop signal handlers.
            pass
    try:
        await client.initialize_components()
        await client.idle()
    except asyncio.CancelledError:
        client.logger.info("Shutting down...")
    finally:
        for sig in registered:
            loop.remove_signal_handler(sig)
        await client.stop_task()


def main() -> None:
    """Start the bot and let asyncio close its event loop after cleanup."""
    client.logger.info("Starting TgMusicBot...")
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        pass
    except Exception:
        client.logger.critical("Fatal error", exc_info=True)
        raise


if __name__ == "__main__":
    main()
