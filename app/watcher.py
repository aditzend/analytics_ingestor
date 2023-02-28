import time
from watchdog.observers import Observer
from watchdog_handler import Handler
import logging


class Watcher:
    def __init__(self, path):
        self.path = path
        self.event_handler = Handler()
        self.observer = Observer()
        self.logger = logging.getLogger(__name__)

    def start(self):
        self.logger.info(f"Starting watcher on {self.path}")
        self.observer.schedule(self.event_handler, self.path, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            self.observer.stop()
            self.observer.join()
