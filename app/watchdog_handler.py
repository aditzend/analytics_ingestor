from watchdog.events import FileSystemEventHandler
import logging
import process
from pathlib import Path
import os


class Handler(FileSystemEventHandler):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_path = os.getenv("CALL_RECORDINGS_PATH")
        self.processed_path = os.getenv("PROCESSED_PATH")
        self.error_path = os.getenv("ERROR_PATH")
        self.split_path = os.getenv("SPLIT_PATH")
        self.nlp_path = os.getenv("NLP_PATH")

    def on_created(self, event):

        if not event.is_directory:
            if self.processed_path in event.src_path:
                self.logger.info(f"File created in processed path {event}")
            elif self.error_path in event.src_path:
                self.logger.error(f"File created in failed path  {event}")
            elif self.nlp_path in event.src_path:
                self.logger.warn(f"File created in NLP path {event}")
                path = Path(event.src_path)
                process.nlp(path)
            elif self.split_path in event.src_path:
                self.logger.debug(f"File created in split path {event}")
            else:
                self.logger.debug(event)
                path = Path(event.src_path)
                process.full(path)

    def on_moved(self, event):

        if not event.is_directory:
            if self.processed_path in event.dest_path:
                self.logger.info(f"Moved to processed {event}")
            elif self.error_path in event.dest_path:
                path = Path(event.src_path)
                process.fail(path)
                self.logger.error(f"Moved to failed dir  {event}")
            elif self.nlp_path in event.dest_path:
                self.logger.warning(f"Reprocessing only NLP {event}")
                path = Path(event.dest_path)
                process.nlp(path)
            elif self.split_path in event.dest_path:
                self.logger.error(f"Moved to split dir {event}")
            else:
                path = Path(event.dest_path)
                self.logger.warning(
                    f"Reprocessing transcription and NLP {event}"
                )
                process.full(path)
