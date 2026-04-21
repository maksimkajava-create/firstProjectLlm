"""RabbitMQ: публикация задач в очередь (как в примере lesson5 — отдельный модуль rm)."""
import json
import logging
import os

import pika

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
QUEUE_NAME = "ml_tasks"


def get_connection():
    """Соединение с брокером."""
    params = pika.URLParameters(RABBITMQ_URL)
    return pika.BlockingConnection(params)


def publish_task(message: dict) -> None:
    """Отправка сообщения в очередь."""
    connection = get_connection()
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2),
    )

    logging.info(f"[Publisher] Сообщение отправлено в очередь: {message['task_id']}")
    connection.close()
