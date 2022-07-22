# REQUIREMENTS
# For table: pip install azure-data-tables

from typing import Any, Dict, List, Optional
from azure.data.tables import TableServiceClient, TableClient
import uuid
import sys

# Default values
DEFAULT_FILE_PATH = "C:/Users/mlou/Documents/cosmos practice/myTestDB/values.txt"
DEFAULT_TABLE_NAME = "ncydconfigurationinfo"
DEFAULT_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=ncydtabledb;AccountKey=BgxGmRqfcRSU79yTwXFaU8xY20vEcfD9kRpRvoeickozvdqhGutqz0Bq7qNSBpBPGinQLQSr2obU036m1Foq5w==;TableEndpoint=https://ncydtabledb.table.cosmos.azure.com:443/;"


def parse_data(path):
    out = {}

    with open(path, 'r') as file:
        for line in file:
            # Split into two parts
            key_value = line.split(" = ")

            # Get rid of newline characters
            key_value[0] = key_value[0].replace("\n", "")
            key_value[1] = key_value[1].replace("\n", "")
            
            # Strip the extra quatations
            if(key_value[0][0] == '"' and key_value[0][-1] == '"'):
                out[key_value[0]] = key_value[1][1:-1]
            if(key_value[1][0] == '"' and key_value[1][-1] == '"'):
                out[key_value[0]] = key_value[1][1:-1]
    
    # To be determined (these two fields are required, both need to be strings)
    # PartitionKey + RowKey combination needs to be unique
    out["PartitionKey"] = "pkey"
    out["RowKey"] = str(uuid.uuid4())
    
    return out


def parse_bytes(text_bytes:bytes):
    out = {}

    text = text_bytes.decode("utf-8")

    for line in text.split("\n"):
        # Get rid of newline and carriage return characters
        line.replace("\n", "")
        line.replace("\r", "")

        # Split into two parts
        key_value = line.split(" = ")
        
        # Strip the extra quatations
        if(key_value[0][0] == '"' and key_value[0][-1] == '"'):
            out[key_value[0]] = key_value[1][1:-1]
        if(key_value[1][0] == '"' and key_value[1][-1] == '"'):
            out[key_value[0]] = key_value[1][1:-1]
    
    # To be determined (these two fields are required, both need to be strings)
    # PartitionKey + RowKey combination needs to be unique
    out["PartitionKey"] = "pkey"
    out["RowKey"] = str(uuid.uuid4())
    
    return out


def connect_to_db(conn_str:str):
    return TableServiceClient.from_connection_string(conn_str)


def connect_to_table(client:TableServiceClient, table_name:str):
    return client.create_table_if_not_exists(table_name)


def upsert_entry(table:TableClient, entry:Dict[str, Any]):
    table.upsert_entity(entry)


def delete_entry(table:TableClient, partition_key:str, row_key:str):
    table.delete_entity(partition_key, row_key)


def get_entry(table:TableClient, partition_key:str, row_key:str):
    return table.get_entity(partition_key, row_key)


def query(table:TableClient, query:Optional[str]=None, fields:Optional[List[str]]=None):
    # query_filter = None means return all items
    # select = None means return all columns
    # fields is a list of strings, which are the requested fields
    return table.query_entities(query_filter=query, select=fields)


def publish(text_path:str, connection_string:str, table_name:str):
    entry = parse_data(text_path)
    database = connect_to_db(connection_string)
    table = connect_to_table(database, table_name)
    upsert_entry(table, entry)


def run():
    try:
        text_path = sys.argv[1]
    except:
        text_path = DEFAULT_FILE_PATH
    try:
        connection_string = sys.argv[2]
    except:
        connection_string = DEFAULT_CONNECTION_STRING
    try:
        table_name = sys.argv[3]
    except:
        table_name = DEFAULT_TABLE_NAME
    
    publish(text_path, connection_string, table_name)



# MAIN
if(__name__ == "__main__"):
    run()
