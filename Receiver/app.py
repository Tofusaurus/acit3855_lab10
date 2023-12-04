import connexion
from connexion import NoContent
import yaml
import logging
import logging.config
import uuid
import json
from pykafka import KafkaClient
import datetime
import time

# # Load app and log configuration
# with open('app_conf.yml', 'r') as f:
#     app_config = yaml.safe_load(f.read())


# with open('log_conf.yml', 'r') as f:
#     log_config = yaml.safe_load(f.read())
# logging.config.dictConfig(log_config)

# logger = logging.getLogger('basicLogger')

import os
if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"

else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"

with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())

# External Logging Configuration
with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)    

# Initialize Kafka client using the configuration file
hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
logger.info(f"Connecting to kafka '{hostname}'")


max_retries = app_config['retries']['max_attempts']
sleep_time_sec = app_config['retries']['sleep_time_sec']

retry_count = 0
while retry_count < max_retries:
    # Display an info log message indicating you are trying to connect to Kafka and the current
    # retry count
    logger.info(f"Trying to connect to Kafka. Retry Count: {retry_count}")

    try:
        client = KafkaClient(hosts=hostname)
        topic = client.topics[str.encode(app_config["events"]["topic"])]
        logger.info(f"Connected to Kafka '{hostname}'")
        break
    except Exception as e:
        # Display an error log message indicating that the connection failed
        logger.error(f"Connection failed to Kafka.  Retry Count: {retry_count}. Error: {str(e)}")

        # Sleep for the configured sleep time and then increment the retry count
        time.sleep(sleep_time_sec)
        retry_count += 1


def send_to_kafka(event_type, event):
    producer = topic.get_sync_producer()

    msg = {
        "type": event_type,
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": event
    }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))
    print("sent to Kafka")

# Function to handle adding inventory
def add_inventory(body):
    trace_id = str(uuid.uuid4())
    logger.info(f"Received event add_inventory request with a trace id of {trace_id}")
    body['trace_id'] = trace_id

    # Define the event type for adding inventory
    event_type = 'add_inventory'

    # Send the message to Kafka
    send_to_kafka(event_type, body)

    # Return a hard-coded status code of 201 since we are not making an HTTP request
    return NoContent, 201

# Function to handle updating inventory
def update_inventory(body):
    trace_id = str(uuid.uuid4())
    logger.info(f"Received event update_inventory request with a trace id of {trace_id}")
    body['trace_id'] = trace_id

    # Define the event type for updating inventory
    event_type = 'update_inventory'

    # Send the message to Kafka
    send_to_kafka(event_type, body)

    # Since we are not getting a status code from an HTTP request, we hard-code it to 201
    return NoContent, 201

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8080)