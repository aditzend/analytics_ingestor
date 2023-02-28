import shutil
import logging
import os
import logging
import requests
import json
from dotenv import load_dotenv
from pathlib import Path
import datetime

load_dotenv()

logger = logging.getLogger(__name__)


processed_path = os.getenv("PROCESSED_PATH") or "./processed"
error_path = os.getenv("ERROR_PATH")
basepath = Path(os.getenv("CALL_RECORDINGS_PATH") or "/app_data/processed")
split_path = os.getenv("SPLIT_PATH")

analytics_manager_url = os.getenv("ANALYTICS_MANAGER_URL")
analytics_dbinterface_url = os.getenv("ANALYTICS_DBINTERFACE_URL")


def mark_as_processed(ch, method, properties, body):
    # logger.critical(f" [x] Received {body}")
    message = json.loads(body.decode())
    # logger.critical(f" [x] Received {message}")
    audio_url = (
        "/Users/alexander/Downloads/calls/210614222408193_ACD_00001.mp3"
    )

    try:

        job = message["data"]
        audio_url = job["transcription"]["audio_url"]
        logger.info(f"ALL FINISHED : {job['interaction_id']}")
        markTranscriptJobAsFinishedDto = {
            "interaction_id": job["interaction_id"],
            "transcription_job_id": job["transcription"][
                "transcription_job_id"
            ],
            "utterances": job["transcription"]["utterances"],
        }
        requests.post(
            f"{os.getenv('ANALYTICS_MANAGER_URL')}/v3/jobs/finished",
            json=markTranscriptJobAsFinishedDto,
        )

        entity_string = ""
        for entity in job["nlp"]["entities"]:
            entity_string += f"{entity},"
        # TODO : This is a hack, we need to fix this in the future

        # get time in iso string
        now = datetime.datetime.now().isoformat()

        createAnalyticsInteractionDto = {
            "interaction_id": job["interaction_id"],
            "processed_at": now,
            "main_sentiment": job["nlp"]["main_sentiment"],
            "main_emotion": job["nlp"]["main_emotion"],
            "main_intent_group": job["nlp"]["main_intent_group"],
            "main_intent_subgroup": job["nlp"]["main_intent_subgroup"],
            "hate_speech_flag": job["nlp"]["hate_speech_flag"],
            "neg_sentiment_flag": job["nlp"]["neg_sentiment_flag"],
            "joy_emotion_flag": job["nlp"]["joy_emotion_flag"],
            "sadness_emotion_flag": job["nlp"]["sadness_emotion_flag"],
            "anger_emotion_flag": job["nlp"]["anger_emotion_flag"],
            "fear_emotion_flag": job["nlp"]["fear_emotion_flag"],
            "surprise_emotion_flag": job["nlp"]["surprise_emotion_flag"],
            "disgust_emotion_flag": job["nlp"]["disgust_emotion_flag"],
            "entities": entity_string,
        }

        requests.post(
            f"{analytics_dbinterface_url}/v3/interaction",
            json=createAnalyticsInteractionDto,
        )
        for event in job["events"]:
            entity_string = ""
            for entity in event["nlp"]["entities"]:
                entity_string += f"{entity},"

            sentiment_string = ""
            if event["nlp"]["sentiment"]["output"] == "positive":
                sentiment_string = str(
                    event["nlp"]["sentiment"]["probas"]["POS"]
                )
            elif event["nlp"]["sentiment"]["output"] == "negative":
                sentiment_string = "-" + str(
                    event["nlp"]["sentiment"]["probas"]["NEG"]
                )
            else:
                sentiment_string = str(0)
            for sentiment in event["nlp"]["sentiment"]:
                sentiment_string += f"{sentiment},"

            emotion_string = ""
            for emotion in event["nlp"]["emotion"]:
                emotion_string += f"{emotion[0]},"

            ner_string = ""
            for ner in event["nlp"]["ner"]:
                ner_string += f"{ner},"

            pos_string = ""
            for pos in event["nlp"]["pos"]:
                pos_string += f"{pos},"

            hate_speech_string = ""
            for hate_speech in event["nlp"]["hate_speech"]["output"]:
                hate_speech_string += f"{hate_speech},"

            sentiment_score = "0"
            if event["nlp"]["sentiment"]["output"] == "POS":
                sentiment_score = str(
                    event["nlp"]["sentiment"]["probas"]["POS"]
                )
            elif event["nlp"]["sentiment"]["output"] == "NEG":
                sentiment_score = "-" + str(
                    event["nlp"]["sentiment"]["probas"]["NEG"]
                )

            createAnalyticsEventDto = {
                "event_id": event["event_id"],
                "interaction_id": event["interaction_id"],
                "segment_id": event["segment_id"],
                "event_type": event["type"],
                "utterance": event["text"],
                "channel": event["channel"],
                "start_in_ms": event["start"],
                "end_in_ms": event["end"],
                "intention": event["nlp"]["intent"]["intent_name"],
                "entities": entity_string,
                # "sentimientos": event["nlp"]["sentiment"]["output"],
                "sentiment": "0",
                "emotion": event["nlp"]["emotion"]["output"],
                "ner": ner_string,
                "pos": pos_string,
                "hate_speech": hate_speech_string,
            }
            logger.debug(
                f"creating sql event {event['text']} channel:"
                f" {event['channel']}"
            )
            requests.post(
                f"{analytics_dbinterface_url}/v3/event",
                json=createAnalyticsEventDto,
            )

        createAnalyticsEventDto = {}

        shutil.move(audio_url, processed_path)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except shutil.Error as error:
        logging.error(f"{error}")
        raise
    except IOError as error:
        logging.error(f"{error}")
        raise
    except TypeError as error:
        logging.error(f"{error}")
        raise
    except KeyError as error:
        logging.error(f"{error}")
        raise


# connection = pika.BlockingConnection(
#     pika.ConnectionParameters(host="192.168.43.170", port="30072"),
# )

# channel = connection.channel()

# channel.exchange_declare(exchange="asr", exchange_type="topic", durable=True)
# result = channel.queue_declare(
#     queue="transcription-finished", exclusive=False, durable=True
# )

# queue_name = result.method.queue

# channel.queue_bind(
#     exchange="asr",
#     queue=queue_name,
#     routing_key="transcription.finished",
# )
# logger.info(f"Waiting for finishedtranscription jobs on {queue_name}")

# channel.basic_consume(
#     queue=queue_name, on_message_callback=mark_as_processed, auto_ack=False
# )

# channel.start_consuming()
