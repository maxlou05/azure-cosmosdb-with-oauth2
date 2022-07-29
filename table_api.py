# REQUIREMENTS
# For table: pip install azure-data-tables

from typing import Any, Dict, List, Optional
from azure.data.tables import TableServiceClient, TableClient
import uuid
import os

# Default values
DEFAULT_TABLE_NAME = os.environ["TABLE_NAME"]
DEFAULT_CONNECTION_STRING = os.environ["CUSTOMCONNSTR_TABLE"]


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
    
    out["PartitionKey"] = "pkey"
    try:
        out["RowKey"] = out["prefix"]
    except:
        raise Exception("Please provide a key named \"prefix\" with a unique value")
    
    return out


def connect_to_db(conn_str:Optional[str] = None):
    if(conn_str is None):
        return TableServiceClient.from_connection_string(DEFAULT_CONNECTION_STRING)
    return TableServiceClient.from_connection_string(conn_str)


def connect_to_table(db:TableServiceClient, table_name:Optional[str] = None):
    if(table_name is None):
        return db.create_table_if_not_exists(DEFAULT_TABLE_NAME)
    return db.create_table_if_not_exists(table_name)


def upsert_entry(table:TableClient, entry:Dict[str, Any]):
    table.upsert_entity(entry)


def delete_entry(table:TableClient, id:str, partition_key:Optional[str] = None):
    if(partition_key is None):
        table.delete_entity(partition_key="pkey", row_key=id)
    table.delete_entity(partition_key, id)


def get_entry(table:TableClient, id:str, partition_key:Optional[str] = None):
    try:
        if(partition_key is None):
            return table.get_entity(partition_key="pkey", row_key=id)
        return table.get_entity(partition_key=partition_key, row_key=id)
    except:
        return None


def query(table:TableClient, query:Optional[str]=None, fields:Optional[List[str]]=None):
    # query_filter = None means return all items
    # select = None means return all columns
    # fields is a list of strings, which are the requested fields
    return table.query_entities(query_filter=query, select=fields)
