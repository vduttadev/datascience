import os
import sys, traceback

import django
from django.conf import settings
import uuid

import logging

logger = logging.getLogger('control_panel')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
sys.path.append(BASE_DIR + "/control_panel")
logger.info(BASE_DIR)
django.setup()

import json
from pykafka import KafkaClient
from pykafka import SslConfig
from time import sleep
from trad_plan_analysis.runner import analyze_plan
from trad_plan_analysis.models import Message
from pykafka.exceptions import NoBrokersAvailableError, SocketDisconnectedError, LeaderNotFoundError


def get_consumer(host_url, topic_name, zookeeper_url, consumer_group, retry_interval=60):
    logger.info("Attempting to create consumer at host: {0} with topic: {1}, zookeeper: {2}, consumer_group: {3}, ssl_config: {4}".format(
        host_url, topic_name, zookeeper_url, consumer_group, get_ssl_config()))
    client = None
    topic = None
    consumer = None
    ex = None
    try:
        #ssl_config=get_ssl_config()
        #if ssl_config is not None:
        #    client = KafkaClient(host_url, ssl_config)
        #else:
        client = KafkaClient(hosts=host_url)
        topic = client.topics[topic_name]
        consumer = topic.get_balanced_consumer(
            consumer_group=consumer_group,
            auto_commit_enable=True,
            zookeeper_connect=zookeeper_url
        )

    except (NoBrokersAvailableError,SocketDisconnectedError,LeaderNotFoundError) as e:
       errmsg = str(e.args[0])
       logger.info('Failed to create consumer with message %s. Retrying in %s seconds.' % (errmsg, retry_interval))
       sleep(retry_interval)
    except BaseException as e:
       print('ERROR CLASS \t|\t',e.__class__)
       traceback.print_exc()

    return client, topic, consumer


def get_ssl_config():
    if settings.KAFKA_SSL:
        cert_path = BASE_DIR + "/resources/" + settings.KAFKA_SSL
        logger.info("Creating Kafka SSL Config with cert path: {0}".format(cert_path))
        config = SslConfig(
            cafile=cert_path
        )
        return config
    else:
        return None


def get_producer(host_url, topic_outgoing_name):
    client = KafkaClient(hosts=host_url)
    topic = client.topics[topic_outgoing_name]
    producer = topic.get_producer()
    return producer


def sendMessage(m):
    producer = get_producer()


def ingest_message(msg, consumer):
    data = json.loads(msg.value.decode('utf-8'))
    logger.info('Received kafka message: %s offeset: %d' % (str(data), msg.offset))
    x = uuid.UUID(data['requestId'])
    logger.info('message_id=%s status=recieved' % (x))
    message = Message(message_id=x, input_data=data, output_data='', status='recieved')
    logger.info('message_id=%s status=mapping-start' % (x))
    logger.debug('message_id=%s status=mapping-start data=%s offeset=%d' %
                 (x, str(data), msg.offset))
    analyze_plan(data, message, x)
    consumer.commit_offsets()


def main():

    client, topic, consumer = get_consumer(
        host_url=settings.KAFKA_URL,
        topic_name=settings.KAFKA_QUOTING_REQUEST_TOPIC,
        zookeeper_url=settings.KAFKA_ZOOKEEPER_URL,
        consumer_group=settings.KAFKA_CONSUMER_GROUP,
        retry_interval=5
    )
    logger.info('service=Control-Panel-Service status=started-listening')
    logger.info('Consumer created')
    logger.info(consumer)
    for message in consumer:
        if message is not None:
            ingest_message(message, consumer)


if __name__ == '__main__':
    main()
