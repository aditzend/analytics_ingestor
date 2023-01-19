import os
from datetime import datetime
import requests
import logging

logger = logging.getLogger('job')


def post(interaction_id, path, audio_info, transcript_data):
    analytics_url = os.getenv('ANALYTICS_MANAGER_URL')
    currentMinute = datetime.now().strftime("%Y%m%d%H%M")
    asr_provider = os.getenv('DEFAULT_ASR_PROVIDER')
    # TODO: armar las otras posibles variables de asr
    try:
        # traverse all transcript_data.parameters and check if there is a key called
        # 'NombreParametro' with value 'ASR_PROVIDER' and get the value of the key 'ValorParametro'

        if transcript_data['parameters']:
            for param in transcript_data['parameters']:
                if param['NombreParametro'] == 'ASR_PROVIDER':
                    asr_provider = param['Valor']
                    break

        logger.debug(
            f'{interaction_id} provider: {asr_provider} td: {transcript_data}')
        # post = requests.post(analytics_url + '/v3/transcript/job', {
        #     'id': interaction_id + '_TJ_' + currentMinute,
        #     'interaction_id': interaction_id,
        #     'audio_url': path,
        #     'asr_provider': audio_info['asr_provider'],
        # })

        return {
            'testing': True
        }
    except Exception as error:
        logger.error(f'{interaction_id} post() : {error}')


# export class CreateTranscriptJobDto {
#     @ IsNotEmpty()
#     @ IsString()
#     id: string; // mongoose.Schema.Types.ObjectId,
#     @ IsNotEmpty()
#     @ IsString()
#     interaction_id: string; // mongoose.Schema.Types.ObjectId,
#     @ IsNotEmpty()
#     audio_url: string;
#     @ IsString()
#     asr_provider: string;
#     @ IsString()
#     asr_language?: string;
#     @ IsNumber()
#     sample_rate?: number;
#     @ IsNumber()
#     n_samples: number;
#     @ IsNumber()
#     channels?: number;
#     @ IsNumber()
#     duration?: number;
#     @ IsString()
#     audio_format?: string;
#     @ IsBoolean()
#     is_silent?: boolean; }
