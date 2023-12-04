import sqlite3

conn = sqlite3.connect('inventory.sqlite')

c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS inventory
    (id INTEGER PRIMARY KEY ASC,
     item_id VARCHAR(250) NOT NULL, 
     product_name VARCHAR(250) NOT NULL,
     storage_date DATETIME NOT NULL,
     stored_by VARCHAR(250) NOT NULL,
     weight FLOAT NOT NULL,
     quantity INTEGER,
     location VARCHAR(250),
     trace_id VARCHAR(36) NOT NULL,  # Added trace_id column
     date_created DATETIME NOT NULL
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS update_inventory
    (id INTEGER PRIMARY KEY ASC, 
     item_id VARCHAR(250) NOT NULL,
     product_name VARCHAR(250),
     storage_date DATETIME,
     stored_by VARCHAR(250),
     weight FLOAT,
     quantity INTEGER,
     location VARCHAR(250),
     trace_id VARCHAR(36) NOT NULL,  # Added trace_id column
     date_updated DATETIME NOT NULL
    )
''')

conn.commit()
conn.close()