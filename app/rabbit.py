import pika
import logging
import os
from dotenv import load_dotenv

load_dotenv()


class RabbitMQ:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.host = os.getenv("RABBITMQ_HOST") or ""
        self.port = os.getenv("RABBITMQ_PORT") or 0
        self.transcript_exchange = (
            os.getenv("RABBITMQ_TRANSCRIPT_EXCHANGE") or ""
        )
        self.all_finished_exchange = (
            os.getenv("RABBITMQ_ALL_FINISHED_EXCHANGE") or ""
        )
        self.all_finished_queue = (
            os.getenv("RABBITMQ_ALL_FINISHED_QUEUE") or ""
        )
        self.publish_connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                client_properties={
                    "connection_name": "transcription-job-connection"
                },
            )
        )
        self.consume_connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                client_properties={
                    "connection_name": "all-finished-connection"
                },
            )
        )

    def publish_transcript_job(
        self,
        message,
        routing_key,
    ):
        try:
            channel = self.publish_connection.channel()
            channel.exchange_declare(
                self.transcript_exchange,
                exchange_type="topic",
                durable=True,
            )

            channel.basic_publish(
                exchange=self.transcript_exchange,
                routing_key=routing_key,
                body=message,
            )
            self.logger.info(
                f"Published message to {self.transcript_exchange}"
            )
            self.publish_connection.close()

        except IOError as error:
            self.logger.error(f"Error publishing message: {error}")
            raise

    def consume_finished(self, callback):
        try:
            channel = self.consume_connection.channel()

            channel.exchange_declare(
                exchange=self.all_finished_exchange,
                exchange_type="fanout",
                durable=True,
            )

            result = channel.queue_declare(
                queue=self.all_finished_queue, exclusive=False, durable=True
            )

            queue_name = result.method.queue

            channel.queue_bind(
                exchange=self.all_finished_exchange,
                queue=queue_name,
                routing_key="all.*.finished.*",
            )
            self.logger.info(f"Waiting for transcription jobs on {queue_name}")

            channel.basic_consume(
                queue=queue_name, on_message_callback=callback, auto_ack=False
            )

            channel.start_consuming()
        except IOError as error:
            self.logger.error(f"Error: {error}")
            raise
