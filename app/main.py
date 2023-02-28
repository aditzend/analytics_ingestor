import os
from pathlib import Path
import logging
import coloredlogs
from dotenv import load_dotenv

import process
import sentry_sdk
import threading
from watcher import Watcher

from rabbit import RabbitMQ
from handle_finished import mark_as_processed

# import consume


load_dotenv()

sentry_sdk.init(
    dsn="https://602815c171204e69b5052e052adbd5ce@o4504566931062785.ingest.sentry.io/4504566936567808",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
)


FORMAT = (
    "[INGESTOR] - %(asctime)s %(levelname)7s %(module)-20s "
    "%(threadName)-10s %(message)s "
)
logging.basicConfig(level=logging.INFO, format=FORMAT)
coloredlogs.install(level="INFO", fmt=FORMAT)
logger = logging.getLogger("main")

base_path = Path(os.getenv("CALL_RECORDINGS_PATH") or "/app_data/processed")


# host = os.getenv("REDIS_HOST")
# port = os.getenv("REDIS_PORT")
# pool = redis.ConnectionPool(host=host, port=port, db=0)
# redis = redis.Redis(connection_pool=pool)

logger.info("Starting ingestor")


files = (entry for entry in base_path.iterdir() if entry.is_file())
# mp3s = 0
# wavs = 0
# redis.set("mp3s", mp3s)
# redis.set("wavs", wavs)

for path in files:
    process.full(path)
    # logger.info("file found")

# watch()

# consume finished transcriptions


# logger.info(f"Found {mp3s} mp3s and {wavs} wavs")

# Observe path forever
watcher = Watcher(base_path)
# watcher.start()

watcher_thread = threading.Thread(target=watcher.start)
watcher_thread.start()


# Por si hay que escuchar mensajes de rabbitmq
# Pero el message handler le va a dar el ack antes de que este lo vea
rabbit = RabbitMQ()

rabbit.consume_finished(mark_as_processed)


# fq = FinishedQueue()

# fq.consume()
# rabbitmq_thread = threading.Thread(target=fq.consume())
# rabbitmq_thread.start()
