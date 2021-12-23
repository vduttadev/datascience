from django.conf import settings
from pykafka import KafkaClient
import json


producer = None


def get_producer():
    global producer
    if producer is None:
        client = KafkaClient(hosts=settings.KAFKA_URL)
        topic = client.topics[settings.KAFKA_QUOTING_RESULT_TOPIC]
        producer = topic.get_sync_producer()
    return producer


def produce_plan_finished(existing_plan):
    producer = get_producer()

    msg = {}
    msg['opportunityId'] = existing_plan.opportunity.id
    msg['benefitPlanId'] = existing_plan.id
    data = json.dumps(msg).encode('utf-8')
    producer.produce(data)
