from typing import Optional, List, Dict
from fastapi import FastAPI, File, Form, Response, UploadFile, status
from pydantic import BaseModel
import table_api

app = FastAPI()

class Query(BaseModel):
    connection_string : str
    table_name : str
    query : Optional[str]
    fields : Optional[List[str]]

# class Entry(BaseModel):
#     connection_string : str
#     table_name : str

class Entity(BaseModel):
    connection_string : str
    table_name : str
    partition_key : str
    row_key : str


@app.get("/")
def get_root():
    return {"Welcome" : "to the FastAPI version"}


@app.post("/api/query", status_code=status.HTTP_200_OK)
async def api_query(query:Query):
    db = table_api.connect_to_db(query.connection_string)
    table = table_api.connect_to_table(db, query.table_name)
    query_results = list(table_api.query(table, query.query, query.fields))
    return {"Query results" : query_results}


@app.post("/api/publish", status_code=status.HTTP_201_CREATED)
async def api_publish(connection_string:str = Form(), table_name:str = Form(), my_file:UploadFile = File()):
    content = await my_file.read()
    db = table_api.connect_to_db(connection_string)
    table = table_api.connect_to_table(db, table_name)
    entry = table_api.parse_bytes(content)
    table_api.upsert_entry(table, entry)
    return {"message" : "Successfully published deployment with PartitionKey \"{}\" and RowKey \"{}\" to table \"{}\"!".format(entry["PartitionKey"], entry["RowKey"], table_name)}


@app.post("/api/get", status_code=status.HTTP_200_OK)
def api_get(entity:Entity, response:Response):
    db = table_api.connect_to_db(entity.connection_string)
    table = table_api.connect_to_table(db, entity.table_name)
    entry = table_api.get_entry(table, entity.partition_key, entity.row_key)
    if(entry is not None):
        return {"Entry" : entry}
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"message" : "No entity found with the specified PartitionKey and RowKey"}


@app.post("/api/delete", status_code=status.HTTP_200_OK)
def api_delete(entity:Entity, response:Response):
    db = table_api.connect_to_db(entity.connection_string)
    table = table_api.connect_to_table(db, entity.table_name)
    table_api.delete_entry(table, entity.partition_key, entity.row_key)
    return {"message" : f"Successfully deleted entry with PartitionKey \"{entity.partition_key}\" and RowKey \"{entity.row_key}\""}
