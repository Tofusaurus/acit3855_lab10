import mysql.connector

db_conn = mysql.connector.connect(host="fzhukafka.westus3.cloudapp.azure.com", user="dbuser", password="Canada34$", database="events")

db_cursor = db_conn.cursor()

db_cursor.execute('''
DROP TABLE inventory, update_inventory
''')
db_conn.commit()
db_conn.close()