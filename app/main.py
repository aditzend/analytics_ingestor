import time
import os
from pathlib import Path
from process import mp3_process
import logging
import coloredlogs
from dotenv import load_dotenv
import redis
import pickle
from audio_check import audio_info
from transcript import transcript_data
import job

load_dotenv()

FORMAT = '[INGESTOR] %(process)d  - %(asctime)s     %(levelname)s [%(module)s] %(message)s'
# logging.Formatter(FORMAT, "%m/%d/%Y, %H:%M:%S ")
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
coloredlogs.install(level='DEBUG', fmt=FORMAT)
logger = logging.getLogger('main')


processed_path = os.getenv('PROCESSED_PATH')
error_path = os.getenv('ERROR_PATH')
basepath = Path(os.getenv('CALL_RECORDINGS_PATH'))


# Create processed folder if it doesn't exist
if not os.path.exists(processed_path):
    os.makedirs(processed_path)

# Create error folder if it doesn't exist
if not os.path.exists(error_path):
    os.makedirs(error_path)


host = os.getenv('REDIS_HOST')
port = os.getenv('REDIS_PORT')
pool = redis.ConnectionPool(host=host, port=port, db=0)
redis = redis.Redis(connection_pool=pool)

while True:

    files = (entry for entry in basepath.iterdir() if entry.is_file())
    mp3s = 0
    wavs = 0

    for item in files:
        path = str(item)
        interaction_id = item.stem
        # redis.delete(interaction_id)
        # redis.delete(f'{interaction_id}_audio_info')
        # redis.delete(f'{interaction_id}_transcript_data')
        if path.endswith('.mp3'):
            mp3s += 1
            status = redis.get(interaction_id)
            if status is None:
                redis.set(interaction_id, 'CHECKING_AUDIO')
                logger.info(f'{interaction_id}: CHECKING_AUDIO')
            elif status == b'CHECKING_AUDIO':
                audio_info = audio_info(interaction_id, path)
                if audio_info:
                    audio_obj = pickle.dumps(audio_info)
                    redis.set(f'{interaction_id}_audio_info', audio_obj)
                    redis.set(
                        interaction_id, 'GETTING_TRANSCRIPTION_PARAMS')
                    logger.info(
                        f'{interaction_id}: GETTING_TRANSCRIPTION_PARAMS')
            elif status == b'GETTING_TRANSCRIPTION_PARAMS':
                transcript_params = transcript_data(interaction_id)
                if transcript_params:
                    transcript_obj = pickle.dumps(transcript_params)
                    redis.set(f'{interaction_id}_transcript_data',
                              transcript_obj)
                    status = redis.set(interaction_id, 'ANALYZING')
                    logger.info(f'{interaction_id}: ANALYZING')
            elif status == b'ANALYZING':
                audio_info = pickle.loads(
                    redis.get(f'{interaction_id}_audio_info'))
                transcript_params = pickle.loads(
                    redis.get(f'{interaction_id}_transcript_data'))
                post_job = job.post(interaction_id, path,
                                    audio_info, transcript_params)
                if post_job:
                    redis.set(interaction_id, 'PROCESSED')
                logger.info(f'{interaction_id}: PROCESSED')
            elif status == b'PROCESSED':

                logger.info(f'{interaction_id}: PROCESSED')

        if path.endswith('.wav'):
            wavs += 1
    logger.info(f'QUEUE: {mp3s} mp3, {wavs} wav ')
    time.sleep(int(os.getenv('POLLING_INTERVAL')))
