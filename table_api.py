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


def parse_bytes(text_bytes:bytes) -> Dict[str, Any]:
    out = {}

    text = text_bytes.decode("utf-8")

    for line in text.split("\n"):
        # Get rid of newline and carriage return characters
        line = line.replace("\r", "")

        # Split into two parts (key and value)
        key_value = line.split(" = ")
        
        # Strip the extra quatations
        if(key_value[0][0] == '"' and key_value[0][-1] == '"'):
            key_value[0] = key_value[0][1:-1]
        if(key_value[1][0] == '"' and key_value[1][-1] == '"'):
            key_value[1] = key_value[1][1:-1]
    
        out[key_value[0]] = key_value[1]
    
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
    try:
        return table.get_entity(partition_key, row_key)
    except:
        return None


def query(table:TableClient, query:Optional[str]=None, fields:Optional[List[str]]=None):
    # query_filter = None means return all items
    # select = None means return all columns
    # fields is a list of strings, which are the requested fields
    return table.query_entities(query_filter=query, select=fields)
