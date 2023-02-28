import os
from datetime import datetime
import requests
import logging
import pika
from pika.exceptions import AMQPConnectionError
import json
from requests.exceptions import (
    ConnectionError,
    HTTPError,
    Timeout,
    RequestException,
)
import dotenv
import alert
from rabbit import RabbitMQ

dotenv.load_dotenv()


class InteractionNotCreated(Exception):
    """Raised when interaction is not created"""

    pass


class JobRejected(Exception):
    """Raised when job is not created"""

    pass


class JobPending(Exception):
    """Raised when job is pending"""

    pass


class AnalyticsManagerError(Exception):
    """Raised when analytics manager returns a 500 response"""

    pass


class JobInProgress(Exception):
    """Raised when job is in progress"""

    pass


class InteractionConflict(Exception):
    """Raised when interaction is already found in MongoDB"""

    pass


class NlpJob:
    def __init__(
        self,
        interaction_id: str,
    ):
        self.interaction_id = interaction_id
        self.logger = logging.getLogger(__name__)
        self.analytics_url = os.getenv("ANALYTICS_MANAGER_URL") or ""
        self.rabbit = RabbitMQ()

    def post(self):
        try:
            transcription = requests.get(
                f"{self.analytics_url}/v3/transcription/{self.interaction_id}"
            )
            transcription = transcription.json()

            job_data = {
                "transcription_job_id": self.interaction_id,
                "pipeline": transcription["pipeline"],
                "utterances": transcription["utterances"],
            }

        except IOError as error:
            self.logger.error(f"Error: {error}")
            alert.error(
                interaction_id=self.interaction_id,
                description=f"Error: {error}",
            )


class Job:
    def __init__(
        self,
        campaign_name: str,
        segment_number: str,
        interaction_id: str,
        audio_url: str,
        audio_info: dict,
        transcript_data: dict,
        audio_format: str,
    ):
        self.campaign_name = campaign_name
        self.segment_number = segment_number
        self.interaction_id = interaction_id
        self.audio_url = audio_url
        self.base_path = os.getenv("CALL_RECORDINGS_PATH") or ""
        self.audio_info = audio_info
        self.transcript_data = transcript_data
        self.asr_provider: str = os.getenv("DEFAULT_ASR_PROVIDER") or "WHISPER"
        self.asr_language: str = os.getenv("DEFAULT_ASR_LANGUAGE") or "es"
        self.audio_format = audio_format
        self.logger = logging.getLogger(__name__)
        self.analytics_url = os.getenv("ANALYTICS_MANAGER_URL") or ""
        self.rabbitmq_host = os.getenv("RABBITMQ_HOST") or ""
        self.rabbitmq_port = os.getenv("RABBITMQ_PORT") or 0
        self.rabbit = RabbitMQ()

    def is_pending(self):
        try:
            pending_transcript = requests.get(
                f"{self.analytics_url}/v3/transcript/pending/{self.interaction_id}"
            )
            if pending_transcript.content:
                raise JobPending(
                    "Transcription Job with id"
                    f" [{pending_transcript.json()['transcription_job_id']}]"
                    " is already in progress"
                )

        except JobPending as error:
            self.logger.exception(f"Error: {error}")
            alert.warning(
                interaction_id=self.interaction_id,
                description=f"Error: {error}",
            )
            return True
        else:
            return False

    def post(self):

        try:

            currentSecond = datetime.now().strftime("%Y%m%d%H%M%S")

            if "ASR_PROVIDER" in self.transcript_data:
                self.asr_provider: str = self.transcript_data["ASR_PROVIDER"]

            if "ASR_LANGUAGE" in self.transcript_data:
                self.asr_language: str = self.transcript_data["ASR_LANGUAGE"]

            self.job_data = {
                "transcription_job_id": self.interaction_id
                + "_TJ_"
                + currentSecond,
                "base_path": self.base_path,
                "campaign_name": self.campaign_name,
                "segment_number": self.segment_number,
                "interaction_id": self.interaction_id,
                "audio_url": self.audio_url,
                "asr_provider": self.asr_provider,
                "asr_language": self.asr_language,
                "sample_rate": int(self.audio_info["sample_rate"]),
                "num_samples": int(self.audio_info["num_samples"]),
                "channels": int(self.audio_info["channels"]),
                "duration": float(self.audio_info["duration"]),
                "audio_format": self.audio_format,
                "is_silent": self.audio_info["is_silent"],
            }

            # Create a transcript in MongoDb
            job_post_on_analytics = requests.post(
                self.analytics_url + "/v3/transcript/job",
                json=self.job_data,
            )
            # if not job_post_on_analytics:
            #     raise RequestException("Request to analytics manager failed")

            if job_post_on_analytics.status_code == 409:
                raise JobInProgress("Job is already in progress")

            if job_post_on_analytics.status_code == 400:
                raise JobRejected("Job Post Failed with code 400")

            if job_post_on_analytics.status_code == 500:
                raise AnalyticsManagerError(
                    "Analytics Manager returned code 500"
                )

            # Create an interaction in MongoDB
            interaction_post_on_analytics = requests.post(
                f"{self.analytics_url}/v3/interaction/auto",
                json={
                    "id": self.interaction_id,
                },
            )
            if (
                interaction_post_on_analytics.status_code != 409
                and interaction_post_on_analytics.status_code != 201
            ):
                raise InteractionNotCreated("Interaction could not be created")

            # Emit the job to RabbitMQ ASR Exchange
            if self.audio_info["duration"] > 120000:
                self.emit(duration_group="long")
            else:
                self.emit(duration_group="short")
        except JobPending as error:
            self.logger.error(f"[{self.interaction_id}] {error}")
            alert.error(interaction_id=self.interaction_id, description=error)
        except JobRejected as error:
            self.logger.exception(f"[{self.interaction_id}] {error}")
            alert.error(interaction_id=self.interaction_id, description=error)

        except AnalyticsManagerError as error:
            self.logger.error(f"[{self.interaction_id}] {error}")
            alert.error(interaction_id=self.interaction_id, description=error)

        except JobInProgress as error:
            self.logger.error(f"[{self.interaction_id}] {error}")
            alert.error(interaction_id=self.interaction_id, description=error)

        except InteractionConflict as error:
            self.logger.error(f"[{self.interaction_id}] {error}")
            alert.error(interaction_id=self.interaction_id, description=error)

        except InteractionNotCreated as error:
            self.logger.error(f"[{self.interaction_id}] {error}")
            alert.error(interaction_id=self.interaction_id, description=error)

        except TypeError as error:
            self.logger.error(f"[{self.interaction_id}] {error}")
            alert.error(interaction_id=self.interaction_id, description=error)

        except RequestException as error:
            self.logger.error(f"[{self.interaction_id}] {error}")
            alert.error(interaction_id=self.interaction_id, description=error)

        else:
            return True
        finally:
            self.logger.info(f"[{self.interaction_id}] Done processing")

    def emit(self, duration_group="short", processor="gpu"):
        try:
            asr_provider = self.asr_provider.lower()

            routing_key = (
                f"transcribe.{duration_group}.{asr_provider}.{processor}"
            )

            message = {
                "pattern": {
                    "cmd": "transcribe",
                    "duration_group": f"{duration_group}",
                    "asr_provider": f"{self.asr_provider}",
                    "processor": f"{processor}",
                },
                "data": self.job_data,
            }
            self.rabbit.publish_transcript_job(
                message=json.dumps(message), routing_key=routing_key
            )
            # channel.basic_publish(
            #     exchange="asr",
            #     routing_key=routing_key,
            #     body=json.dumps(message),
            # )
            self.logger.exception(
                f"[{self.interaction_id}] Transcript Job emitted to RabbitMQ"
                f" (routing_key={routing_key}, exchange=asr"
            )

        except AMQPConnectionError as error:
            self.logger.error(error)
            alert.error(interaction_id=self.interaction_id, description=error)
