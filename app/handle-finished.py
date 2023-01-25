import shutil
import logging
import os
import pika
import logging
import requests
import json
import coloredlogs
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()

FORMAT = (
    "[INGESTOR] %(process)d  - %(asctime)s     %(levelname)s [%(module)s]"
    " %(message)s"
)
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
coloredlogs.install(level="DEBUG", fmt=FORMAT)
logger = logging.getLogger(__name__)


processed_path = os.getenv("PROCESSED_PATH")
error_path = os.getenv("ERROR_PATH")
basepath = Path(os.getenv("CALL_RECORDINGS_PATH"))
split_path = os.getenv("SPLIT_PATH")


def mark_as_processed(ch, method, properties, body):
    processed_path = os.getenv("PROCESSED_PATH")
    message = json.loads(body.decode())
    job = message["data"]
    logger.error(f"Marking job as processed: {job}")
    # markTranscriptJobAsFinishedDto = {
    #     "interaction_id": job["interaction_id"],
    #     "id": job["id"],
    #     "utterances": job["utterances"],
    # }
    try:
        # requests.post(
        #     f"{os.getenv('ANALyTICS_MANAGER_URL')}/v3/jobs/finished",
        #     json=markTranscriptJobAsFinishedDto,
        # )
        shutil.move(job["audio_url"], processed_path)
        return True
    except Exception as error:
        logging.error(f"{error}")
        return None


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="192.168.43.170", port="30072"),
)

channel = connection.channel()

channel.exchange_declare(exchange="asr", exchange_type="topic", durable=True)
result = channel.queue_declare(
    queue="transcription-finished", exclusive=False, durable=True
)

queue_name = result.method.queue

channel.queue_bind(
    exchange="asr",
    queue=queue_name,
    routing_key="transcription.finished",
)
logger.info(f"Waiting for finishedtranscription jobs on {queue_name}")

channel.basic_consume(
    queue=queue_name, on_message_callback=mark_as_processed, auto_ack=False
)

channel.start_consuming()
