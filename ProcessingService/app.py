import connexion
from connexion import NoContent
import yaml
import logging.config
import json
import os
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import requests  # Make sure to import requests
from flask_cors import CORS, cross_origin


# # Load configurations
# with open('app_conf.yml', 'r') as f:
#     app_config = yaml.safe_load(f.read())

# with open('log_conf.yml', 'r') as f:
#     log_config = yaml.safe_load(f.read())
#     logging.config.dictConfig(log_config)

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

# Helper functions to get and set the last inventory check time
LAST_CHECK_FILE = 'last_check.txt'

def get_last_check_time():
    if not os.path.isfile(LAST_CHECK_FILE):
        return datetime.min
    with open(LAST_CHECK_FILE, 'r') as file:
        return datetime.fromisoformat(file.readline().strip())

def set_last_check_time(check_time):
    with open(LAST_CHECK_FILE, 'w') as file:
        file.write(check_time.isoformat())

def process_inventory():
    logger.info("Start Periodic Processing")

    try:
        with open("inventory_data.json", "r") as file:
            inventory_data = json.loads(file.read())
    except FileNotFoundError:
        inventory_data = {
            "num_inventories": 0,
            "num_updates": 0  # Adding a counter for updates
        }

    last_check_time = get_last_check_time()
    current_timestamp = datetime.utcnow()

    # Base URL from the configuration
    eventstore_base_url = app_config['eventstore']['url']

    # URL for the /inventory endpoint
    inventory_url = f"{eventstore_base_url}/inventory"
    # URL for the /inventory/update endpoint
    inventory_update_url = f"{eventstore_base_url}/inventory/update"

    # First request to /inventory
    response = requests.get(f"{inventory_url}?start_timestamp={last_check_time.isoformat()}&end_timestamp={current_timestamp.isoformat()}")
    if response.status_code == 200:
        new_inventory_items = response.json()
        inventory_data["num_inventories"] += len(new_inventory_items)

    # Second request to /inventory/update
    response_update = requests.get(f"{inventory_update_url}?start_timestamp={last_check_time.isoformat()}&end_timestamp={current_timestamp.isoformat()}")
    logger.info(f"Request to /inventory/update: {inventory_update_url}?start_timestamp={last_check_time.isoformat()}&end_timestamp={current_timestamp.isoformat()}")
    logger.info(f"Response status from /inventory/update: {response_update.status_code}")
    logger.info(f"Response from /inventory/update: {response_update.json()}")
    if response_update.status_code == 200:
        updated_inventory_items = response_update.json()
        logger.info(f"Number of updated items: {len(updated_inventory_items)}")
        inventory_data["num_updates"] += len(updated_inventory_items)  # Increment updates counter

    # After processing both endpoints, set the last check time to the current time
    set_last_check_time(current_timestamp)
    inventory_data["last_updated"] = str(current_timestamp)

    # Dump data back to json file
    with open('inventory_data.json', 'w') as f:
        json.dump(inventory_data, f)

    logger.info("End Periodic Processing")

def get_inventory():
    logger.info("Request for inventory data received")
    try:
        with open(app_config['datastore']['filename'], 'r') as f:
            inventory_data = json.load(f)
        logger.info("Inventory data sent to client")
        return inventory_data, 200
    except FileNotFoundError:
        logger.error("Inventory data file not found")
        return NoContent, 404

# Set up the Flask app
app = connexion.FlaskApp(__name__, specification_dir='./')
logger.info("Adding the API from the openapi.yml specification")
try:
    CORS(app.app)
    app.app.config['CORS_HEADERS'] = 'Content-Type'
    app.add_api('openapi.yml')
    logger.info("The API was added successfully")
except Exception as e:
    logger.error(f"An error occurred while adding the API: {e}")
    raise

# Initialize scheduler
def init_scheduler():
    sched = BackgroundScheduler()

    # Get the current time
    now = datetime.now()

    # Add a job to start immediately
    sched.add_job(process_inventory,
                  'interval',
                  seconds=app_config['scheduler']['period_sec'],
                  start_date=now)  # start_date is now, so the job starts immediately

    sched.start()

def create_default_inventory_file():
    if not os.path.isfile(app_config['datastore']['filename']):
        dirname = os.path.dirname(app_config['datastore']['filename'])
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)
        logger.info("Creating default " + app_config['datastore']['filename'] + " file")
        default_data = {
            "num_inventories": 0,
            "num_updates": 0
        }
        with open(app_config['datastore']['filename'], 'w') as f:
            json.dump(default_data, f)

if __name__ == '__main__':
    logger.info('Processing Service is starting up.')
    create_default_inventory_file()  # Check and create default inventory file
    init_scheduler()
    app.run(port=8100)