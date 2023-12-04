import logging.config
import connexion
from connexion import NoContent
from pykafka import KafkaClient
import json
import yaml
from flask_cors import CORS, cross_origin


# # Load the app config file
# with open('app_conf.yml', 'r') as f:
#     app_config = yaml.safe_load(f.read())

# # Load the log config file
# with open('log_conf.yml', 'r') as f:
#     log_config = yaml.safe_load(f.read())
# logging.config.dictConfig(log_config)

# # Create a logger from the basicLogger defined in the configuration file.
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

# Establishing connection to Kafka server and setting the topic.
def get_kafka_client():
    logger.info(f"Connecting to Kafka '{app_config['events']['hostname']}:{app_config['events']['port']}'")
    client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    logger.info(f"Connected to Kafka {app_config['events']['hostname']}:{app_config['events']['port']}")
    return client


def get_event_by_index(event_type, index):
    """ 
    Generic function to retrieve an event based on its type and relative index.
    """
    
    client = get_kafka_client()
    topic = client.topics[app_config['events']['topic']]
        
    # Initializing a Kafka consumer
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    
    # Logging the retrieval attempt.
    logger.info(f"Retrieving {event_type} at index {index}")
    
    #print([
    #    msg.value.decode('utf-8') for msg in consumer
    #])
    
    try:
        count = 0
        for msg in consumer:

            if msg:
                msg_str = msg.value.decode('utf-8')
                msg_dict = json.loads(msg_str)
                
                if msg_dict['type'] == event_type:
                    if count == index:
                        return msg_dict["payload"], 200
                    count += 1
        
        logger.error(f"No more messages found or could not find {event_type} at index {index}")
        return {"message": "Not Found"}, 404
    except Exception as e:
        logger.error(f"Error retrieving {event_type} at index {index}: {e}")
        return {"message": "Internal Server Error"}, 500

def get_add_inventory_reading(index):
    """ Retrieves an event1 from Kafka based on its relative index. """
    return get_event_by_index('add_inventory', index)

def get_update_inventory_reading(index):
    """ Retrieves an event2 from Kafka based on its relative index. """
    return get_event_by_index('update_inventory', index)

# Create the application instance
app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8110)
