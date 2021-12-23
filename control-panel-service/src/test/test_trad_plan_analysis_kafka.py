import json
import os
import sys
import uuid


from pykafka import KafkaClient
# from django.conf import settings

dir_path = os.path.dirname(os.path.realpath(__file__))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
sys.path.append(BASE_DIR + "./resources")
print(BASE_DIR)
# django.setup()

client = KafkaClient("kafka:9092")
topic = client.topics["opportunity.current_plan_evaluated"]

f = open(os.path.join(dir_path, 'data/traditional_plan_v0_response.json'))
msg_data = f.read()
f.close()

with topic.get_producer() as producer:
    producer.produce(msg_data.encode('utf-8'))

print('sent quoting request')

print('test done')
