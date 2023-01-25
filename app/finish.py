import shutil
import logging
import os
import pika
import logging


logger = logging.getLogger("finish")

# def consume(queue_name="whisper_transcription_jobs"):
#     connection = pika.BlockingConnection(
#         pika.ConnectionParameters(host="192.168.43.170", port="30072"),
#     )

#     channel = connection.channel()

#     channel.exchange_declare(
#         exchange="asr", exchange_type="topic", durable=True
#     )
#     result = channel.queue_declare(
#         queue="whisper-finished-jobs", exclusive=False, durable=True
#     )

#     queue_name = result.method.queue

#     channel.queue_bind(
#         exchange="asr",
#         queue=queue_name,
#         routing_key="transcription.finished",
#     )
#     logger.info(f"Waiting for finishedtranscription jobs on {queue_name}")

#     channel.basic_consume(
#         queue=queue_name, on_message_callback=run_dual_sox, auto_ack=False
#     )

#     channel.start_consuming()


def processed(path):
    processed_path = os.getenv("PROCESSED_PATH")
    try:
        shutil.move(path, processed_path)
        return True
    except Exception as error:
        logging.error(f"{error}")
        return None
