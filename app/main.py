import time
import os
from pathlib import Path
import logging
import coloredlogs
from dotenv import load_dotenv
import redis
import pickle
from audio import audio_info, split_channels
from transcript import transcript_data
import job
import finish
import sys

load_dotenv()

FORMAT = (
    "[INGESTOR] %(process)d  - %(asctime)s     %(levelname)s [%(module)s]"
    " %(message)s"
)
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
coloredlogs.install(level="DEBUG", fmt=FORMAT)
logger = logging.getLogger("main")


processed_path = os.getenv("PROCESSED_PATH")
error_path = os.getenv("ERROR_PATH")
basepath = Path(os.getenv("CALL_RECORDINGS_PATH"))
split_path = os.getenv("SPLIT_PATH")
polling_interval = int(os.getenv("POLLING_INTERVAL")) or 5
# Create processed folder if it doesn't exist
if not os.path.exists(processed_path):
    os.makedirs(processed_path)

# Create error folder if it doesn't exist
if not os.path.exists(error_path):
    os.makedirs(error_path)

# Create split folder if it doesn't exist
if not os.path.exists(split_path):
    os.makedirs(split_path)


host = os.getenv("REDIS_HOST")
port = os.getenv("REDIS_PORT")
pool = redis.ConnectionPool(host=host, port=port, db=0)
redis = redis.Redis(connection_pool=pool)

logger.info("Starting ingestor")

# Observe path forever
while True:
    try:
        files = (entry for entry in basepath.iterdir() if entry.is_file())
        mp3s = 0
        wavs = 0

        for item in files:
            path = str(item)
            interaction_id = item.stem
            id_as_string = item.stem
            logger.critical(
                f"Processing {interaction_id}, type"
                f" item.stem:{type(item.stem)} type"
                f" item:{type(item)} type"
                f" iid:{type(id_as_string)}"
                f" interaction_id:{type(interaction_id)}"
            )
            if path.endswith(".mp3") and type(item.stem) == str:
                mp3s += 1
                status = redis.get(interaction_id)
                if status is None:
                    redis.set(interaction_id, "GETTING_TRANSCRIPTION_PARAMS")
                    logger.info(
                        f"{interaction_id}: GETTING_TRANSCRIPTION_PARAMS"
                    )

                elif status == b"GETTING_TRANSCRIPTION_PARAMS":
                    logger.critical(
                        f"GETTING_TRANSCRIPTION_PARAMS {interaction_id}, "
                        f" item.stem:{type(item.stem)} type"
                        f" item:{type(item)} type"
                        f" iid:{type(id_as_string)}"
                        f" interaction_id:{type(interaction_id)}"
                    )
                    transcript_params = transcript_data(
                        interaction_id=interaction_id
                    )
                    if transcript_params:
                        transcript_obj = pickle.dumps(transcript_params)
                        redis.set(
                            f"{interaction_id}_transcript_data", transcript_obj
                        )
                        status = redis.set(interaction_id, "CHECKING_AUDIO")
                        logger.info(f"{interaction_id}: CHECKING_AUDIO")
                elif status == b"CHECKING_AUDIO":
                    transcript_data = pickle.loads(
                        redis.get(f"{interaction_id}_transcript_data")
                    )
                    logger.debug(f"{interaction_id}: {transcript_data}")
                    asr_provider = transcript_data["ASR_PROVIDER"]
                    audio_info = audio_info(interaction_id, path)
                    if audio_info:
                        audio_obj = pickle.dumps(audio_info)
                        redis.set(f"{interaction_id}_audio_info", audio_obj)
                        redis.set(interaction_id, "POSTING_JOB")
                        logger.info(f"{interaction_id}: POSTING_JOB")
                # elif status == b'SPLITTING_CHANNELS':
                #     split_channels(interaction_id, path)
                #     if split_channels:
                #         redis.set(interaction_id, 'POSTING_JOB')
                #         logger.info(f'{interaction_id}: POSTING_JOB')
                elif status == b"POSTING_JOB":
                    audio_info = pickle.loads(
                        redis.get(f"{interaction_id}_audio_info")
                    )
                    transcript_params = pickle.loads(
                        redis.get(f"{interaction_id}_transcript_data")
                    )
                    post_job = job.post(
                        interaction_id,
                        path,
                        audio_info,
                        transcript_params,
                        "mp3",
                    )
                    if not post_job:
                        redis.set(interaction_id, "POST_JOB_ERROR")
                        logger.info(f"{interaction_id}: POST_JOB_ERROR")
                    else:
                        redis.set(interaction_id, "PROCESSING")
                        logger.info(f"{interaction_id}: PROCESSING")
                elif status == b"POST_JOB_ERROR":
                    audio_info = pickle.loads(
                        redis.get(f"{interaction_id}_audio_info")
                    )
                    transcript_params = pickle.loads(
                        redis.get(f"{interaction_id}_transcript_data")
                    )
                    post_job = job.post(
                        interaction_id,
                        path,
                        audio_info,
                        transcript_params,
                        "mp3",
                    )
                    if post_job:
                        redis.set(interaction_id, "PROCESSING")
                    logger.info(f"{interaction_id}: PROCESSING")
                elif status == b"TRANSCRIPTION_FINISHED":
                    finished = finish.processed(path)
                    if finished:
                        redis.delete(interaction_id)
                        redis.delete(f"{interaction_id}_audio_info")
                        redis.delete(f"{interaction_id}_transcript_data")
                        # TODO: Move file to processed folder
                        logger.info(
                            f"{interaction_id}: TRANSCRIPTION_FINISHED"
                        )
                    else:
                        logger.error(f"{interaction_id}: Could not move file")
            interaction_id = id_as_string

            if path.endswith(".wav"):
                wavs += 1
    except Exception as error:
        type, value, traceback = sys.exc_info()
        logger.error(f"Error: {error}")

    logger.info(f"QUEUE: {mp3s} mp3, {wavs} wav ")
    time.sleep(int(os.getenv("POLLING_INTERVAL")))
