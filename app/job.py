import os
from datetime import datetime
import requests
import logging
import pika
import json

logger = logging.getLogger("job")


def post(interaction_id, path, audio_info, transcript_data, audio_format):
    analytics_url = os.getenv("ANALYTICS_MANAGER_URL")
    currentMinute = datetime.now().strftime("%Y%m%d%H%M")
    # asr_provider = os.getenv('DEFAULT_ASR_PROVIDER')
    # asr_language = os.getenv('DEFAULT_ASR_LANGUAGE')
    # TODO: armar las otras posibles variables de asr
    try:
        # traverse all transcript_data.parameters and check if there is a key called
        # 'NombreParametro' with value 'ASR_PROVIDER' and get the value of the key 'ValorParametro'

        # if transcript_data['parameters']:
        #     for param in transcript_data['parameters']:
        #         if param['NombreParametro'] == 'ASR_PROVIDER':
        #             asr_provider = param['Valor']
        #         if param['NombreParametro'] == 'ASR_LANGUAGE':
        #             asr_language = param['Valor']
        #             break

        # check if ASR_PROVIDER is a key in transcript_data
        if "ASR_PROVIDER" in transcript_data:
            asr_provider = transcript_data["ASR_PROVIDER"]
        else:
            asr_provider = os.getenv("DEFAULT_ASR_PROVIDER")

        # check if ASR_LANGUAGE is a key in transcript_data
        if "ASR_LANGUAGE" in transcript_data:
            asr_language = transcript_data["ASR_LANGUAGE"]
        else:
            asr_language = os.getenv("DEFAULT_ASR_LANGUAGE")

        job_data = {
            "id": interaction_id + "_TJ_" + currentMinute,
            "base_path": os.getenv("CALL_RECORDINGS_PATH"),
            "interaction_id": interaction_id,
            "audio_url": path,
            "asr_provider": asr_provider,
            "asr_language": asr_language,
            "sample_rate": int(audio_info["sample_rate"]),
            "num_samples": int(audio_info["num_samples"]),
            "channels": int(audio_info["channels"]),
            "duration": float(audio_info["duration"]),
            "audio_format": audio_format,
            "is_silent": audio_info["is_silent"],
        }

        # Create a transcript in MongoDb
        post = requests.post(
            analytics_url + "/v3/transcript/job", json=job_data
        )

        # Create an interaction in MongoDB
        interaction = requests.post(
            f"{analytics_url}/v3/interaction/{interaction_id}/auto"
        )

        logger.debug(f"{interaction_id} POST /v3/transcript/job : {post}")
        if post.status_code == 201:
            logger.info(f"{interaction_id} POST /v3/transcript/job : OK")
            emit(job=job_data)
            return True
        else:
            logger.error(
                f"{interaction_id} POST /v3/transcript/job : {post.text}"
            )
            return False
    except Exception as error:
        logger.error(f"{interaction_id} post() : {error}")


def emit(job):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host="192.168.43.170",
            port="30072",
        )
    )
    channel = connection.channel()

    channel.exchange_declare(
        exchange="asr", exchange_type="topic", durable=True
    )

    routing_key = "transcribe.short.whisper.cpu"

    message = {
        "pattern": {
            "cmd": "transcribe",
            "group": "short",
            "type": "whisper",
            "device": "cpu",
        },
        "data": job,
    }

    channel.basic_publish(
        exchange="asr",
        routing_key=routing_key,
        body=json.dumps(message),
    )
    connection.close()
