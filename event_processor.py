from confluent_kafka import Consumer, Producer
import redis
import json

# Kafka configurations
KAFKA_BROKER = 'localhost:9092'
EVENT_TOPIC = 'events'
RESULT_TOPIC = 'results'

# Redis configurations
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# Initialize Redis client
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Function to process an event
def process_event(event):
    try:
        # Deserialize event
        event_data = json.loads(event)
        number = event_data['number']

        # Perform a calculation (e.g., square the number)
        result = number ** 2

        # Cache the result in Redis
        redis_key = f"event:{number}"
        redis_client.set(redis_key, result)

        return result
    except Exception as e:
        print(f"Error processing event: {e}")
        return None

# Initialize Kafka consumer
consumer_config = {
    'bootstrap.servers': KAFKA_BROKER,
    'group.id': 'recalc_group',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(consumer_config)

# Subscribe to the event topic
consumer.subscribe([EVENT_TOPIC])

# Initialize Kafka producer
producer_config = {'bootstrap.servers': KAFKA_BROKER}
producer = Producer(producer_config)

try:
    print("Starting event processor...")
    while True:
        # Poll for messages
        msg = consumer.poll(1.0)  # Timeout of 1 second

        if msg is None:
            continue  # No message received

        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue

        # Process the event
        event = msg.value().decode('utf-8')
        print(f"Received event: {event}")
        result = process_event(event)

        if result is not None:
            # Send the result to the results topic
            result_event = {'number': json.loads(event)['number'], 'result': result}
            producer.produce(RESULT_TOPIC, json.dumps(result_event))
            print(f"Sent result: {result_event}")

        # Flush producer to ensure delivery
        producer.flush()

except KeyboardInterrupt:
    print("Shutting down event processor...")
finally:
    consumer.close()
