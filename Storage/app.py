import connexion
from connexion import NoContent
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from base import Base
from inventory_item import InventoryItem
from update_inventory import UpdateInventoryItem
import yaml
import logging.config
import logging
import json
import time
from datetime import datetime
from flask import request
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
import mysql.connector
from mysql.connector import Error

# # Load app and log configuration
# with open('app_conf.yml', 'r') as f:
#     app_config = yaml.safe_load(f.read())

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

# Access specific configuration settings
db_user = app_config['datastore']['user']
db_password = app_config['datastore']['password']
db_hostname = app_config['datastore']['hostname']
db_port = app_config['datastore']['port']
db_name = app_config['datastore']['db']
max_retries = app_config['retries']['max_attempts']
sleep_time_sec = app_config['retries']['sleep_time_sec']

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

# Database setup
DB_ENGINE = create_engine(f'mysql+pymysql://{db_user}:{db_password}@{db_hostname}:{db_port}/{db_name}')
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)

logger.info(f"Connecting to DB. Hostname:{db_hostname}, Port:{db_port}.")



def add_inventory(body):
    """ Receives an inventory item record """
    session = DB_SESSION()
    inventory_item = InventoryItem(
        item_id=body['item_id'],
        product_name=body['product_name'],  # Changed from item_name to product_name
        quantity=body['quantity'],
        trace_id=body['trace_id']
    )
    session.add(inventory_item)
    session.commit()
    session.close()

    logger.debug(f"Stored event add_inventory request with a trace id of {body['trace_id']}")
    return NoContent, 201


def get_inventory():
    """ Retrieves warehouse inventory """
    session = DB_SESSION()
    start_timestamp = request.args.get('start_timestamp', default=None)
    end_timestamp = request.args.get('end_timestamp', default=None)
    query = session.query(InventoryItem)

    if start_timestamp and end_timestamp:
        try:
            start_timestamp_datetime = datetime.fromisoformat(start_timestamp)
            end_timestamp_datetime = datetime.fromisoformat(end_timestamp)
            query = query.filter(
                and_(
                    InventoryItem.date_created >= start_timestamp_datetime,
                    InventoryItem.date_created < end_timestamp_datetime
                )
            )
        except ValueError as ve:
            logger.error(f"Error parsing 'start_timestamp' or 'end_timestamp' parameter: {ve}")
            session.close()
            return {"message": f"Invalid 'start_timestamp' or 'end_timestamp' parameter: {ve}"}, 400

    searchString = request.args.get('searchString', default=None)
    if searchString:
        query = query.filter(InventoryItem.product_name.contains(searchString))

    skip = request.args.get('skip', default=0, type=int)
    limit = request.args.get('limit', default=50, type=int)

    try:
        inventory_items = query.offset(skip).limit(limit).all()
        return [item.to_dict() for item in inventory_items], 200
    except Exception as e:
        logger.error(f"Error fetching inventory items: {e}")
        session.rollback()
        session.close()
        return {"message": f"Error fetching inventory items: {e}"}, 500
    finally:
        session.close()

def update_inventory(body):
    """ Updates an inventory item record """
    session = DB_SESSION()
    storage_date = datetime.strptime(body['storage_date'], "%Y-%m-%dT%H:%M:%S.%fZ") if 'storage_date' in body else None
    update_item = UpdateInventoryItem(
        item_id=body['item_id'],
        product_name=body.get('product_name'),
        storage_date=storage_date,
        stored_by=body.get('stored_by'),
        weight=body.get('weight'),
        quantity=body.get('quantity'),
        location=body.get('location'),
        trace_id=body['trace_id'],  # Make sure to include the trace_id here
        date_updated=datetime.utcnow()
    )


    session.add(update_item)
    session.commit()
    session.close()
    return NoContent, 201

def get_inventory_update():
    """ Retrieves updates to inventory items """
    session = DB_SESSION()
    start_timestamp = request.args.get('start_timestamp', default=None)
    end_timestamp = request.args.get('end_timestamp', default=None)
    query = session.query(UpdateInventoryItem)  # Querying the UpdateInventoryItem table

    if start_timestamp and end_timestamp:
        try:
            start_timestamp_datetime = datetime.fromisoformat(start_timestamp)
            end_timestamp_datetime = datetime.fromisoformat(end_timestamp)
            query = query.filter(
                and_(
                    UpdateInventoryItem.date_updated >= start_timestamp_datetime,
                    UpdateInventoryItem.date_updated < end_timestamp_datetime
                )
            )
        except ValueError as ve:
            logger.error(f"Error parsing 'since' parameter: {ve}")
            session.close()
            return {"message": f"Invalid 'since' parameter: {ve}"}, 400

    searchString = request.args.get('searchString', default=None)
    if searchString:
        query = query.filter(UpdateInventoryItem.product_name.contains(searchString))

    skip = request.args.get('skip', default=0, type=int)
    limit = request.args.get('limit', default=50, type=int)

    try:
        update_items = query.offset(skip).limit(limit).all()
        return [item.to_dict() for item in update_items], 200  # Ensure UpdateInventoryItem has a to_dict method or similar
    except Exception as e:
        logger.error(f"Error fetching updated inventory items: {e}")
        session.rollback()
        session.close()
        return {"message": f"Error fetching updated inventory items: {e}"}, 500
    finally:
        session.close()

def store_add_inventory(payload):
    """Store event data to the inventory table."""
    query = """
    INSERT INTO inventory (item_id, product_name, quantity, trace_id)
    VALUES (%s, %s, %s, %s)
    """
    try:
        db_conn = mysql.connector.connect(host="fzhukafka.westus3.cloudapp.azure.com", 
                                          user="dbuser", 
                                          password="Canada34$", 
                                          database="events")
        db_cursor = db_conn.cursor()
        db_cursor.execute(query, (payload['item_id'], 
                                  payload['product_name'], 
                                  payload['quantity'], 
                                  payload['trace_id']))
        db_conn.commit()
        logger.info("Inserted add_inventory data to the inventory table")
    except Error as e:
        logger.error(f"Error: {e}")
    finally:
        if db_cursor is not None:
            db_cursor.close()
        if db_conn is not None:
            db_conn.close()

def store_update_inventory(payload):
    """Store event data to the update_inventory table."""
    query = """
    INSERT INTO update_inventory (item_id, product_name, storage_date, stored_by, weight, quantity, location, trace_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    # Extract data from payload with proper error checking
    item_id = payload.get('item_id')
    product_name = payload.get('product_name')
    storage_date = payload.get('storage_date') 
    stored_by = payload.get('stored_by')
    weight = payload.get('weight')
    quantity = payload.get('quantity')
    location = payload.get('location')
    trace_id = payload.get('trace_id')

    try:
        db_conn = mysql.connector.connect(host="fzhukafka.westus3.cloudapp.azure.com", 
                                          user="dbuser", 
                                          password="Canada34$", 
                                          database="events")
        db_cursor = db_conn.cursor()
        # Execute the insert statement with the payload data
        db_cursor.execute(query, (item_id, product_name, storage_date, stored_by, weight, quantity, location, trace_id))
        db_conn.commit()
        logger.info("Inserted update_inventory data to the update_inventory table")
    except mysql.connector.Error as e:
        logger.error(f"Error: {e}")
    finally:
        if db_cursor is not None:
            db_cursor.close()
        if db_conn is not None:
            db_conn.close()

def process_messages():
    """ Process event messages """
    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    logger.info(f"Connecting to Kafka. Hostname:{hostname}")

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

    consumer = topic.get_simple_consumer(consumer_group=b'event_group',
                                         reset_offset_on_start=False,
                                         auto_offset_reset=OffsetType.LATEST)

    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s" % msg)
        payload = msg["payload"]
        
        # Assuming you have functions to store to DB called `store_event1` and `store_event2`
        if msg["type"] == "add_inventory":
            store_add_inventory(payload)
        elif msg["type"] == "update_inventory":
            store_update_inventory(payload)

        consumer.commit_offsets()

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()  
    app.run(port=8090)