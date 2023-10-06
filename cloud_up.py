import os
import logging
import adodbapi
import mysql.connector
from google.cloud import storage

# LOGGING SETUP
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

def connect_to_mysql(host, db_name, user, password):
    ''' 
    Connect to MySQL and return the connection and cursor.
    '''
    mysql_connection = mysql.connector.connect(
        host=host,
        database=db_name,
        user=user,
        password=password
    )

    if not mysql_connection.is_connected():
        raise ConnectionError("Failed to connect to the MySQL database")

    mysql_cursor = mysql_connection.cursor()
    return mysql_connection, mysql_cursor

def connect_to_sqlce(data_source):
    ''' 
    Connect to SQLCE and return the connection and cursor.
    '''
    conn_str = f'Provider=Microsoft.SQLSERVER.CE.OLEDB.4.0; Data Source={data_source};'
    sqlce_connection = adodbapi.connect(conn_str)
    sqlce_connection.connector.CursorLocation = 2  # Adjusting CursorLocation for buffered mode
    sqlce_cursor = sqlce_connection.cursor()
    return sqlce_connection, sqlce_cursor


def generate_paths(cursor, job_id, job_name):
    '''
    generate path from SQLCE with job_id
    recreate cloud path by job_name
    return: list of local paths, list of cloud paths
    '''
    
    related_query = f"SELECT name, OrderIndex FROM ScanArea WHERE AcquireSettings_id={job_id} AND Enabled=1"
    cursor.execute(related_query)
    related_records = cursor.fetchall()

    local_paths = []
    cloud_paths = []

    for related_record in related_records:
        scan_name = related_record[0]
        order_index = related_record[1]

        if "Continue" in job_name:
            words = job_name.split()
            parent_folder = ' '.join(words[:-2])
            sub_folder = ' '.join(words[-2:])
            path = os.path.join(parent_folder, scan_name, sub_folder)
        else:
            path = os.path.join(job_name, scan_name, "Primary")

        local_path = os.path.join(str(job_id), "Acquire_0", str(order_index))

        local_paths.append(local_path)
        cloud_paths.append(path)

    return local_paths, cloud_paths





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

def list_buckets(service_account_file):
    # Instantiates a storage client with the service account file
    storage_client = storage.Client.from_service_account_json(service_account_file)

    # Lists all the buckets
    buckets = list(storage_client.list_buckets())

    for bucket in buckets:
        print(bucket.name)

def copy_to_cloud(local_path, cloud_path, service_account_file_path, bucket_name):
    """
    Copy data from local path to Google Cloud Storage.
    
    local_path: The path on your local machine.
    cloud_path: The desired path in GCS where data will be stored.
    service_account_file_path: Path to your service account json file.
    bucket_name: Name of the GCS bucket where data will be uploaded.
    """
    
    # Check if local path exists
    storage_client = storage.Client.from_service_account_json(service_account_file_path)
    bucket = storage_client.bucket(bucket_name)

    # Walk through all files in the local directory
    for dirpath, dirnames, filenames in os.walk(local_path):
        for filename in filenames:
            local_file = os.path.join(dirpath, filename)
            # Create the full cloud path for this file
            cloud_file_path = os.path.join(cloud_path, os.path.relpath(local_file, local_path)).replace(os.sep, '/')
            blob = bucket.blob(cloud_file_path)
            
            # Check if the blob exists in GCS
            if not blob.exists():
                blob.upload_from_filename(local_file)
                store_paths(mysql_cursor, job_id, local_path, cloud_path)
                print('copy:',local_path,'to cloud:',cloud_path)
            else:
                print(f"File {cloud_file_path} already exists in GCS. Skipping upload.")



def main():
    global mysql_connection
    # Database configs
    db_host = "34.78.59.186"
    db_name = "met_db"
    db_user = "root"
    db_password = "Metsystem"
    service_account_file_path = 'met-raw-images.json'
    bucket_name = "ocelloscope_raw"
    data_source = "DataStore.sdf"

    # Create a connection to the database

    try:
        # Connect to databases
        mysql_connection, mysql_cursor = connect_to_mysql(db_host, db_name, db_user, db_password)
        sqlce_connection, sqlce_cursor = connect_to_sqlce(data_source)
        
        storage_client = storage.Client.from_service_account_json(service_account_file_path)
        bucket = storage_client.bucket(bucket_name)

        if mysql_connection.is_connected():
            print("Connected to the database")
            print(list_buckets(service_account_file_path))
        else:
            print("Failed to connect to the database")
            
        
        # Fetching data from SQL CE Job table
        query_job = "SELECT * FROM Job"
        sqlce_cursor.execute(query_job)
        results = sqlce_cursor.fetchall()

        logger = setup_logger()
        # skip the last job, save time
        last_uploaded_id = get_last_uploaded_job_id()
        for job in results:
            job = list(job)  # job[0] is Job_id
            job_id = job[0]

            if job_id <= last_uploaded_id:
                continue


            local_paths, cloud_paths = generate_paths(sqlce_cursor, job_id, job[1])

            files_exist = False 

            # If local data exists, copy it to the cloud
            for local_path, cloud_path in zip(local_paths, cloud_paths):
                if not os.path.exists(local_path):
                    logger.warning(f"Error: Local path {local_path} does not exist. Skipping.")
                    continue
                copy_to_cloud(local_path, cloud_path, service_account_file_path, bucket_name) 
                files_exist = True

            if not files_exist:
                continue

            try:
                insert_query = f"INSERT INTO Job VALUES ({', '.join(['%s'] * len(job))})"
                mysql_cursor.execute(insert_query, job)
                mysql_connection.commit()  # Changed from mysql_connection to mysql_conn

                # Use insert_data_into_mysql function for inserting data to tables 

                insert_data_into_mysql(sqlce_cursor, mysql_cursor, "JobTask", "Job_id", job_id)
                insert_data_into_mysql(sqlce_cursor, mysql_cursor, "JobEvent", "Job_id", job_id)
                insert_data_into_mysql(sqlce_cursor, mysql_cursor, "AcquireTask", "JobTask_id", job_id)
                insert_data_into_mysql(sqlce_cursor, mysql_cursor, "AcquireSettings", "OriginalAcquireTask_id", job_id)
                insert_data_into_mysql(sqlce_cursor, mysql_cursor, "InstrumentInformation", "Id", job_id)
                insert_data_into_mysql(sqlce_cursor, mysql_cursor, "ScanArea", "AcquireSettings_id", job_id)

            except mysql.connector.IntegrityError as ie:
                logger.error(f"Error inserting data for Job ID {job_id}: {ie}")
                continue
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")  
    finally:
        # Close database connections
        sqlce_cursor.close()
        sqlce_connection.close()
        mysql_cursor.close()
        mysql_connection.close()

        logger.info("Data migration complete.")

if __name__ == "__main__":
    main()