import sox
import shutil
import requests
import logging
import os
import redis

logger = logging.getLogger('audio_check')

analytics_manager_url = os.getenv('ANALYTICS_MANAGER_URL')

host = os.getenv('REDIS_HOST')
port = os.getenv('REDIS_PORT')
pool = redis.ConnectionPool(host=host, port=port, db=0)
redis = redis.Redis(connection_pool=pool)


def audio_info(interaction_id, path):
    try:
        error_path = os.getenv('ERROR_PATH')
        audio_checked = {}
        # path = '/Users/alexander/Downloads/calls/210614222408193_ACD_00001.mp3'
        audio_checked['sample_rate'] = 8000
        audio_checked['num_samples'] = sox.file_info.num_samples(path)
        audio_checked['duration'] = sox.file_info.duration(path)
        audio_checked['is_silent'] = sox.file_info.silent(path)
        audio_checked['channels'] = sox.file_info.channels(path)
        logger.info(f'{interaction_id}: Audio OK')
        return audio_checked
    except Exception as error:
        logger.error(f'{interaction_id}: {error}')
        alert = requests.post(f"{analytics_manager_url}/v3/alert", {
            'id': f"{interaction_id}_FILE_ERROR",
            'severity': 'HIGH',
            'interaction_id': interaction_id,
            'description': f'Ingestion failed for {interaction_id}: {error}',
            'service': 'analytics_ingestor',
            'type': 'FILE_ERROR'
        })
        logger.warning(
            f'{interaction_id}: Alert sent (STATUS_CODE={alert.status_code})')
        shutil.move(path, error_path)
        logger.warning(f'{interaction_id}: Moved {path} to {error_path}')
        redis.delete(interaction_id)
        return None
