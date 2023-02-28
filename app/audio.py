import sox
from sox.core import SoxError
from sox.core import SoxiError
import shutil
import requests
import logging
import os
import redis
from pydub import AudioSegment
import alert

logger = logging.getLogger(__name__)

analytics_manager_url = os.getenv("ANALYTICS_MANAGER_URL")
# host = os.getenv("REDIS_HOST")
# port = os.getenv("REDIS_PORT")
# pool = redis.ConnectionPool(host=host, port=port, db=0)

# redis = redis.Redis(connection_pool=pool)


class AudioError(Exception):
    """File has no audio or cannot be processed"""

    pass


def check_mp3(path):
    interaction_id = path.stem
    file = str(path)
    audio = {}
    try:
        audio["format"] = "mp3"
        audio["sample_rate"] = sox.file_info.sample_rate(file)
        audio["num_samples"] = sox.file_info.num_samples(file)
        audio["duration"] = sox.file_info.duration(file)
        audio["is_silent"] = sox.file_info.silent(file)
        audio["channels"] = sox.file_info.channels(file)
    except SoxiError as error:
        logger.exception(f"[{interaction_id}] SoxiError {error}")
        alert.error(
            interaction_id=interaction_id,
            description=f"Audio could not be processed: {error}",
        )
    except FileNotFoundError as error:
        logger.exception(f"[{interaction_id}] FileNotFoundError {error}")
        alert.error(
            interaction_id=interaction_id,
            description=f"File not found: {error}",
        )
    else:
        return audio
    finally:
        logger.info(f"[{interaction_id}] Audio Check Finished")


def audio_info(interaction_id, path):
    try:
        error_path = os.getenv("ERROR_PATH")
        audio_checked = {}
        # path = '/Users/alexander/Downloads/calls/210614222408193_ACD_00001.mp3'
        audio_checked["sample_rate"] = sox.file_info.sample_rate(path)
        audio_checked["num_samples"] = sox.file_info.num_samples(path)
        audio_checked["duration"] = sox.file_info.duration(path)
        audio_checked["is_silent"] = sox.file_info.silent(path)
        audio_checked["channels"] = sox.file_info.channels(path)
        logger.info(f"{interaction_id}: Audio OK {audio_checked}")
        return audio_checked
    except Exception as error:
        logger.error(f"{interaction_id}: {error}")
        alert = requests.post(
            f"{analytics_manager_url}/v3/alert",
            {
                "id": f"{interaction_id}_FILE_ERROR",
                "severity": "HIGH",
                "interaction_id": interaction_id,
                "description": (
                    f"Ingestion failed for {interaction_id}: {error}"
                ),
                "service": "analytics_ingestor",
                "type": "FILE_ERROR",
            },
        )
        logger.warning(
            f"{interaction_id}: Alert sent (STATUS_CODE={alert.status_code})"
        )
        shutil.move(path, error_path)
        logger.warning(f"{interaction_id}: Moved {path} to {error_path}")
        redis.delete(interaction_id)
        return None


def split_channels(interaction_id, path):
    # TODO: Solo funciona para mp3, hacerlo dinamico para wav o ogg
    try:
        error_path = os.getenv("ERROR_PATH")
        # stereo = AudioSegment.from_file(path, format='mp3')
        # monos = stereo.split_to_mono()
        # mono_left = monos[0].export(f'{path}.left.mp3', format='mp3')

        logger.info(f"{interaction_id}: Channels split")
        return True
    except Exception as error:
        logger.error(f"{interaction_id}: {error}")
        alert = requests.post(
            f"{analytics_manager_url}/v3/alert",
            {
                "id": f"{interaction_id}_FILE_ERROR",
                "severity": "HIGH",
                "interaction_id": interaction_id,
                "description": (
                    f"Ingestion failed for {interaction_id}: {error}"
                ),
                "service": "analytics_ingestor",
                "type": "FILE_ERROR",
            },
        )
        logger.warning(
            f"{interaction_id}: Alert sent (STATUS_CODE={alert.status_code})"
        )
        shutil.move(path, error_path)
        logger.warning(f"{interaction_id}: Moved {path} to {error_path}")
        redis.delete(interaction_id)
        return None
