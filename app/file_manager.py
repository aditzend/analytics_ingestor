import shutil
import logging
import os
from pathlib import Path
import alert
import dotenv

dotenv.load_dotenv()


class FileManager:
    def __init__(self):
        self.processed_path = Path(os.getenv("PROCESSED_PATH") or ".")
        self.error_path = Path(os.getenv("ERROR_PATH") or ".")
        self.split_path = Path(os.getenv("SPLIT_PATH") or ".")
        self.logger = logging.getLogger(__name__)
        # Create processed folder if it doesn't exist
        if not os.path.exists(self.processed_path):
            os.makedirs(self.processed_path)

        # Create error folder if it doesn't exist
        if not os.path.exists(self.error_path):
            os.makedirs(self.error_path)

        # Create split folder if it doesn't exist
        if not os.path.exists(self.split_path):
            os.makedirs(self.split_path)

    def finish(self, path):
        try:
            shutil.move(path, self.processed_path)
        except FileExistsError as error:
            self.logger.exception(f"[{path.stem}] {error}")
            alert.error(
                interaction_id=path.stem,
                description=f"File already exists: {error}",
            )
        except FileNotFoundError as error:
            self.logger.exception(f"[{path.stem}] {error}")
            alert.error(
                interaction_id=path.stem,
                description=f"File not found: {error}",
            )
        else:
            self.logger.info(
                f"[{path.stem}] File moved to {self.processed_path} folder"
            )
            return True

    def error(self, path):
        try:
            shutil.move(path, self.error_path)
        except FileExistsError as error:
            self.logger.exception(f"[{path.stem}] {error}")
            alert.error(
                interaction_id=path.stem,
                description=f"File already exists: {error}",
            )
        except FileNotFoundError as error:
            self.logger.exception(f"[{path.stem}] {error}")
            alert.error(
                interaction_id=path.stem,
                description=f"File not found: {error}",
            )
        else:
            self.logger.info(f"[{path.stem}] File moved to {self.error_path}")
            return True
