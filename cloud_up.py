import os
import shutil
import mysql.connector
import adodbapi

def generate_path(cursor, job_id, job_name):
    '''
    return: local path, cloud path

    '''
    related_query = f"SELECT name, OrderIndex FROM ScanArea WHERE AcquireSettings_id={job_id} AND Enabled=1"
    cursor.execute(related_query)
    related_record = cursor.fetchone()

    if related_record:
        scan_name = related_record[0]
        order_index = related_record[1]

        if "Continue" in job_name:
            words = job_name.split()
            parent_folder = ' '.join(words[:-2])
            sub_folder = ' '.join(words[-2:])
            path = f"{parent_folder}/{scan_name}/{sub_folder}"
        else:
            path = f"{job_name}/{scan_name}/Primary"

        return f"{job_id}/Acquire_0/{order_index}", path

    return None, None

def copy_to_cloud(local_path, cloud_path):
    """Simulate copying from local path to cloud."""
    # This is a mock function. 
    if os.path.exists(local_path):
        shutil.copytree(local_path, cloud_path)


def store_paths(destination_cursor, job_id, local_path, cloud_path):
    """Store local and cloud paths in the PathStorage table."""
    insert_query = "INSERT INTO PathStorage (job_id, local_path, cloud_path) VALUES (%s, %s, %s)"
    try:
        destination_cursor.execute(insert_query, (job_id, local_path, cloud_path))
        mysql_connection.commit()
    except Exception as e:
        print(f"Error storing paths for job_id {job_id}: {e}")

# insert_data_into_mysql function and connection code 
def insert_data_into_mysql(source_cursor, destination_cursor, table, column, job_id):
    '''
    source_cursor: the SQLCE cursor where the data from
    destination_cursor: the google MySQL cursor where the date insert
    table: table name 
    job_id: index

    '''

    source_cursor.execute(f"SELECT * FROM {table} WHERE {column} = {job_id}")
    records = source_cursor.fetchall()

    for record in records:
        record = list(record)
        insert_query = f"INSERT INTO {table} VALUES ({', '.join(['%s'] * len(record))})"
        
        try:
            destination_cursor.execute(insert_query, record)
            mysql_connection.commit()
        except mysql.connector.IntegrityError as ie:
            print(f"Error inserting into {table}: {ie}")
            continue


# create an log
def setup_logger(filename="migration_log.txt"):
    ''' 
    Setup a basic logger that writes messages to a file and console.
    '''
    import logging

    # Setting up logging
    logger = logging.getLogger('migration_logger')
    logger.setLevel(logging.DEBUG)

    # File handler for writing logs
    file_handler = logging.FileHandler(filename)
    file_handler.setLevel(logging.DEBUG)

    # Console handler for printing logs
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Setting format for the log messages
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def get_last_uploaded_job_id(filename='last_uploaded.txt'):
    try:
        with open(filename, 'r') as f:
            return int(f.read().strip())
    except FileNotFoundError:
        return 0

def update_last_uploaded_job_id(job_id, filename='last_uploaded.txt'):
    with open(filename, 'w') as f:
        f.write(str(job_id))



# Connect Google MySql
db_host = "34.78.59.186"
db_name = "met_db"
db_user = "root"
db_password = "Metsystem"

# Create a connection to the database
mysql_connection = mysql.connector.connect(
    host=db_host,
    database=db_name,
    user=db_user,
    password=db_password
)

# Check if the connection is established
if mysql_connection.is_connected():
    print("Connected to the database")
else:
    print("Failed to connect to the database")

conn_str = r'Provider=Microsoft.SQLSERVER.CE.OLEDB.4.0; Data Source=DataStore.sdf;'
sqlce_connection = adodbapi.connect(conn_str)
sqlce_connection.connector.CursorLocation = 2
sqlce_cursor = sqlce_connection.cursor()

mysql_cursor = mysql_connection.cursor()

# Fetching data from SQL CE Job table
query_job = "SELECT * FROM Job"
sqlce_cursor.execute(query_job)
results = sqlce_cursor.fetchall()

logger = setup_logger()
# skip the last job, save time
last_uploaded_id = get_last_uploaded_job_id()

for job in results:
    # Insert data to Job table
    job = list(job) #job[0] is Job_id
    job_id = job[0]
    

    if job_id <= last_uploaded_id:
        continue
    
    try:
        insert_query = f"INSERT INTO Job VALUES ({', '.join(['%s'] * len(job))})"
        mysql_cursor.execute(insert_query, job)
        mysql_connection.commit()

        # Use insert_data_into_mysql function for inserting data to tables 
        # Keep the order of inserting since the foreign key constraint
        insert_data_into_mysql(sqlce_cursor, mysql_cursor, "JobTask", "Job_id", job_id)
        insert_data_into_mysql(sqlce_cursor, mysql_cursor, "JobEvent", "Job_id", job_id)
        insert_data_into_mysql(sqlce_cursor, mysql_cursor, "AcquireTask", "JobTask_id", job_id)
        insert_data_into_mysql(sqlce_cursor, mysql_cursor, "AcquireSettings", "OriginalAcquireTask_id", job_id)
        insert_data_into_mysql(sqlce_cursor,mysql_cursor, "InstrumentInformation", "Id", job_id)
        insert_data_into_mysql(sqlce_cursor, mysql_cursor, "ScanArea", "AcquireSettings_id", job_id)

        
        # Generate the paths
        local_path, cloud_path = generate_path(sqlce_cursor, job_id, job[1])

        if not os.path.exists(local_path):
            print(f"Error: Local path {local_path} does not exist. Skipping job {job_id}.")
            continue

        if local_path and cloud_path:
            copy_to_cloud(local_path, cloud_path)  # Simulate copying
            store_paths(mysql_cursor, job_id, local_path, cloud_path)
        
    except mysql.connector.IntegrityError as ie:
        logger.error(f"Error inserting Job: {ie}")
        continue
    
    
# Once the job is successfully uploaded and local data is deleted:
update_last_uploaded_job_id(job_id)

# Close connections
sqlce_cursor.close()
sqlce_connection.close()
mysql_cursor.close()
mysql_connection.close()