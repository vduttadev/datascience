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
topic = client.topics["opportunity.current_plan"]

# f = open(os.path.join(dir_path, 'data/traditional_plan_v0.json'))
f = open(os.path.join(dir_path, 'data/leslie_plan_03.json'))
msg_data = f.read()
f.close()
# uuId = 'a1a0f7b7-b18b-4ba0-971a-eeda916b75da'
uuId = '060b7587-382d-446e-9584-6e0328cd62cc'
requestId = uuid.uuid1()

msg_data = msg_data.replace("$UUID$", str(uuId))
msg_data = msg_data.replace("$REQID$", str(requestId))
with topic.get_producer() as producer:
    producer.produce(msg_data.encode('utf-8'))

print('sent quoting request')

result_topic = client.topics["opportunity.current_plan_evaluated"]
consumer = result_topic.get_simple_consumer()
for message in consumer:
    if message is not None:
        print('received quoting result')
        data = json.loads(message.value.decode('utf-8', 'ignore'))
        print('response:' + str(data))
        assert data['success'] == 'true'
        break
print('test done')
