
import requests
import shutil
import logging
import os
from pathlib import Path
import redis
import pickle
from datetime import datetime

host = os.getenv('REDIS_HOST')
port = os.getenv('REDIS_PORT')
pool = redis.ConnectionPool(host=host, port=port, db=0)
redis = redis.Redis(connection_pool=pool)

logger = logging.getLogger('transcript')


def transcript_data(interaction_id):
    logging.info(f' {interaction_id}: Getting transcript data')
    path = os.getenv('CALL_RECORDINGS_PATH')
    error_path = os.getenv('ERROR_PATH')
    basepath = Path(os.getenv('CALL_RECORDINGS_PATH'))
    analytics_manager_url = os.getenv('ANALYTICS_MANAGER_URL')
    dbinterface_url = os.getenv('DBINTERFACE_URL')
    try:
        result = requests.get(
            f"{dbinterface_url}/v3/transcript_data/{interaction_id}")
        if result.status_code == 200:
            logging.info(f'{interaction_id}: Transcript data retrieved')
            return result.json()
        else:
            logging.error(f'{interaction_id}: {result.status_code}')
            alert = requests.post(analytics_manager_url + '/v3/alert', {
                'id': interaction_id
                + '_DBINTERFACE_ERROR',
                'severity': 'HIGH',
                  'interaction_id': interaction_id,
                  'type': 'DBINTERFACE_ERROR',
                  'service': 'analytics_ingestor',
                  'description': f'{interaction_id}: {result.status_code}'
            })
            logging.warning(
                f'{interaction_id}: Alert sent to analytics_manager (STATUS_CODE={alert.status_code})')
            return None
    except Exception as error:
        logging.error(f'{interaction_id} {error}')
        alert = requests.post(analytics_manager_url + '/v3/alert', {
            'id': interaction_id
            + '_DBINTERFACE_ERROR',
            'severity': 'HIGH',
            'interaction_id': interaction_id,
            'type': 'DBINTERFACE_ERROR',
            'service': 'analytics_ingestor',
              'description': f'{interaction_id}: {error}'
        })
        logging.warning(
            f'{interaction_id}: Alert sent to analytics_manager (STATUS_CODE={alert.status_code})')

        shutil.move(path,
                    error_path)
        redis.delete(interaction_id)
        logging.info(f'Moved: {path} to {error_path}')
