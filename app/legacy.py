import time
import shutil
import sox
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
import os
import requests
from datetime import date
from pathlib import Path


# Borrar antes de produccion
os.environ['CALL_RECORDINGS_PATH'] = '/Users/alexander/Downloads/calls'
os.environ['PROCESSED_PATH'] = '/Users/alexander/Downloads/calls/processed'

# Set vars
basepath = Path(os.getenv('CALL_RECORDINGS_PATH')) or Path('.')
processed_path = Path(f'{basepath}/processed')
error_path = Path(f'{basepath}/failed')
transcription_params = {
    'ASR_PROVIDER': 'LOCAL',
    'ASR_LANGUAGE': 'es',
}
dbinterface_url = os.getenv('DBINTERFACE_URL') or 'http://localhost:4000'
analytics_manager_url = os.getenv(
    'ANALYTICS_MANAGER_URL') or 'http://localhost:3000'
# Create processed folder if it doesn't exist
if not os.path.exists(processed_path):
    os.makedirs(processed_path)

# Create error folder if it doesn't exist
if not os.path.exists(error_path):
    os.makedirs(error_path)


while True:
    files = (entry for entry in basepath.iterdir() if entry.is_file())
    mp3s = 0
    wavs = 0
    for item in files:
        # if posixpath ends with .mp3
        path = str(item)
        interaction_id = item.stem

        if path.endswith('.mp3'):
            mp3s += 1
            print(f'{mp3s}: {item}')
            # stereo = AudioSegment.from_file(event.src_path, format='mp3')
            # monos = stereo.split_to_mono()
            # mono_left = monos[0].export(
            #     event.src_path + '-left.mp3', format='mp3')
            try:
                sample_rate = sox.file_info.sample_rate(path)
                n_samples = sox.file_info.num_samples(path)
                duration = sox.file_info.duration(path)
                is_silent = sox.file_info.silent(path)
                channels = sox.file_info.channels(path)
                # print('Sample rate: {}'.format(sample_rate))
                # print('Number of samples: {}'.format(n_samples))
                # print('Duration: {}'.format(duration))
                # print('Is silent: {}'.format(is_silent))
                # print('Channels: {}'.format(channels))

                # Check transcript data for interaction
                try:
                    transcript_data = requests.get(
                        f'{dbinterface_url}/v3/transcript_data/{interaction_id}')
                    if transcript_data.status_code == 200:
                        # Create an interaction in analytics_manager
                        # interaction = requests.get(
                        #     dbinterface_url + '/v3/interaction/full/' + interaction_id)
                        # interaction_data = interaction.json()
                        interaction_in_analytics_manager = requests.post(
                            analytics_manager_url + '/v3/interaction/auto', {'id': interaction_id})
                        # print(
                        #     f'Interaction data: {interaction_in_analytics_manager.text}')
                        # print(f'Transcript data: {transcript_data.text}')
                        parameters = transcript_data.json()['parameters']
                        # if parameters is not empty
                        if parameters:
                            # print(
                            #     f'parameter 0 : {transcript_data.json()["parameters"][0]}')
                            # traverse parameters and check if NombreParametro is a key in transcription_params
                            for parameter in transcript_data.json()['parameters']:
                                if parameter['NombreParametro'] in transcription_params:
                                    # if it is, replace the value with the value in transcription_params
                                    transcription_params[parameter['NombreParametro']
                                                         ] = parameter['Valor']
                                    print(
                                        f'Updated transcription_params: {transcription_params}')

                    else:
                        alert = requests.post(analytics_manager_url + '/v3/alert', {
                            'id': interaction_id
                            + '_INTERACTION_NOT_FOUND',
                            'severity': 'HIGH',
                              'interaction_id': interaction_id,
                              'type': '_INTERACTION_NOT_FOUND',
                              'service': 'analytics_ingestor',
                              'description': f'Transcript data failed for {interaction_id}: {transcript_data.text}'
                        })
                        print(
                            f'Alert sent to analytics_manager:{alert.status_code} {alert.text}')
                        shutil.move(path,
                                    error_path)
                        print(f'Moved: {path} to {error_path}')
                        # print(f'Transcript data: {transcript_data}')
                    # File ok, Interaction ok, create transcript job
                    print(f'Creating transcript job for {interaction_id}')

                    asr_provider = transcription_params['ASR_PROVIDER'] or 'LOCAL'
                    asr_language = transcription_params['ASR_LANGUAGE'] or 'es'
                    # store date_created as the current day
                    date_created = str(date.today())
                    transcript_job = requests.post(analytics_manager_url + '/v3/transcript/job', {
                        'id': interaction_id + asr_provider + asr_language + date_created,
                        'interaction_id': interaction_id,
                        'audio_url': f'{path}',
                        'asr_provider': transcription_params['ASR_PROVIDER'],
                        'asr_language': transcription_params['ASR_LANGUAGE'],
                        'sample_rate': sample_rate,
                        'channels': channels,
                        'n_samples': n_samples,
                        'duration': duration,
                        'is_silent': is_silent,
                        'audio_format': 'mp3'
                    })
                except Exception as error:
                    print(f'Error getting transcript data: {error}')
                    alert = requests.post(analytics_manager_url + '/v3/alert', {
                        'id': interaction_id
                        + '_DBINTERFACE_ERROR',
                        'severity': 'HIGH',
                          'interaction_id': interaction_id,
                          'type': 'DBINTERFACE_ERROR',
                          'service': 'analytics_ingestor',
                          'description': f'Transcript data failed for {interaction_id}: {error}'
                    })
                    print(
                        f'Alert sent to analytics_manager:{alert.status_code} {alert.text}')

                    shutil.move(path,
                                error_path)
                    print(f'Moved: {path} to {error_path}')

            except Exception as error:
                print(f'Sox failed, {error}: {path}')
                alert = requests.post(analytics_manager_url + '/v3/alert', {
                    'id': interaction_id + '_FILE_ERROR',
                    'severity': 'HIGH',
                    'interaction_id': interaction_id,
                    'description': f'Ingestion failed for {interaction_id}: {error}',
                    'service': 'analytics_ingestor',
                    'type': 'FILE_ERROR'
                })
                print(
                    f'Alert sent to analytics_manager:{alert.status_code} {alert.text}')
                shutil.move(path,
                            error_path)
                print(f'Moved: {path} to {error_path}')
                # make an http request to dbinterface alert endpoint
                # move file to processed folder

      # print the count of files in the directory
    print(f'{mp3s} mp3s in queue')
    time.sleep(10)


# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO,
#                         format='%(asctime)s - %(message)s',
#                         datefmt='%Y-%m-%d %H:%M:%S')
#     path = sys.argv[1] if len(sys.argv) > 1 else '.'
#     event_handler = LoggingEventHandler()
#     observer = Observer()
#     observer.schedule(event_handler, path, recursive=False)
#     observer.start()
#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         observer.stop()
#     observer.join()
