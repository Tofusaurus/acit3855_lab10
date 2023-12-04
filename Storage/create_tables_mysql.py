import mysql.connector

# MySQL connection parameters
db_conn = mysql.connector.connect(host="fzhukafka.westus3.cloudapp.azure.com", user="dbuser", password="Canada34$", database="events")

db_cursor = db_conn.cursor()

# Define SQL statements to create the inventory table with the date_created and date_updated columns
create_inventory_table = '''
CREATE TABLE IF NOT EXISTS inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id VARCHAR(250) NOT NULL, 
    product_name VARCHAR(250) NOT NULL,
    storage_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    stored_by VARCHAR(250) NULL,
    weight FLOAT NOT NULL DEFAULT 0,
    quantity INTEGER,
    location VARCHAR(250),
    trace_id VARCHAR(36) NOT NULL,
    date_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
'''

create_update_inventory_table = '''
CREATE TABLE IF NOT EXISTS update_inventory (
    id INT AUTO_INCREMENT PRIMARY KEY, 
    item_id VARCHAR(250) NOT NULL,
    product_name VARCHAR(250) NULL,
    storage_date DATETIME NULL,
    stored_by VARCHAR(250) NULL,
    weight FLOAT NULL DEFAULT 0,
    quantity INTEGER NULL,
    location VARCHAR(250) NULL,
    trace_id VARCHAR(36) NOT NULL,
    date_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
'''

# Execute the SQL statements to create tables
db_cursor.execute(create_inventory_table)
db_cursor.execute(create_update_inventory_table)

# Commit the changes and close the cursor and connection
db_conn.commit()
db_conn.close()
