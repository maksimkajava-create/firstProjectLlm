import os
import sys
import json
import time
import logging
import socket

import pika

from database.connection import SessionLocal
from models.entities import MLTask
from services.crud.ml_task import execute_prediction

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
QUEUE_NAME = "ml_tasks"
WORKER_ID = os.getenv("WORKER_ID", socket.gethostname())

logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s [{WORKER_ID}] %(levelname)s: %(message)s",
    stream=sys.stdout,
)


def connect_with_retry(max_retries=15, delay=3):
    """Подключение к RabbitMQ с максимальным числом попыток и ожиданием между попытками"""
    for attempt in range(1, max_retries + 1):
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
            logging.info("Подключение к RabbitMQ установлено")
            return connection
        except pika.exceptions.AMQPConnectionError:
            logging.warning(f"RabbitMQ недоступен, попытка {attempt}/{max_retries}...")
            time.sleep(delay)
    logging.error("Не удалось подключиться к RabbitMQ")
    sys.exit(1)


def process_message(ch, method, properties, body):
    """Обработка задачи"""
    message = json.loads(body)
    task_uuid = message.get("task_id")
    features = message.get("features")
    prompt = message.get("prompt")
    model_name = message.get("model")

    logging.info(f"Получена задача: {task_uuid}")

    if not task_uuid or not model_name:
        logging.error(f"Невалидное сообщение: {message}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    if not features and not prompt:
        logging.error(f"Нет features и prompt: {message}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return


    try:
        input_data = {}
        if features:
            input_data["features"] = features
        if prompt:
            input_data["prompt"] = prompt

        output_data = execute_prediction(model_name, input_data)
        result_status = "completed"
        logging.info(f"Предсказание {task_uuid} выполнено")
    except Exception as e:
        output_data = {"error": str(e)}
        result_status = "failed"
        logging.error(f"Ошибка предсказания: {e}")

    db = SessionLocal()
    try:
        task = db.query(MLTask).filter(MLTask.task_uuid == task_uuid).first()
        if task:
            task.output_data = output_data
            task.status = result_status
            db.commit()
            logging.info(f"Задача {task_uuid} → {result_status}")
        else:
            logging.error(f"Задача {task_uuid} не найдена в БД")
    except Exception as e:
        logging.error(f"Ошибка записи в БД: {e}")
        db.rollback()
    finally:
        db.close()

    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    logging.info(f"Запуск воркера {WORKER_ID}...")
    connection = connect_with_retry()
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=process_message)
    logging.info("Ожидание задач из очереди...")
    channel.start_consuming()

if __name__ == "__main__":
    main()