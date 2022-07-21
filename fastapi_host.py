from typing import Optional, List, Dict
from fastapi import FastAPI
from pydantic import BaseModel
import table_api

app = FastAPI()

class Query(BaseModel):
    connection_string : str
    table_name : str
    query : Optional[str]
    fields : Optional[List[str]]


class Entry(BaseModel):
    connection_string : str
    table_name : str
    # This needs to be changed later, to just passing the whole text?
    text_path : str


def myQueryFunc(conn_str, table_name, query=None, fields=None):
    db = table_api.connect_to_db(conn_str)
    table = table_api.connect_to_table(db, table_name)
    query_results = list(table_api.query(table, query, fields))
    return {"Query results":query_results}


def myPublishFunc(conn_str, table_name, text_path):
    table_api.publish(text_path, conn_str, table_name)
    return {"message":f"Successfully published deployment to table \"{table_name}\"!"}


@app.get("/")
def get_root():
    return {"Welcome": "to the FastAPI version"}


@app.post("/api/query")
def api_query(query:Query):
    return myQueryFunc(query.connection_string, query.table_name, query.query, query.fields)


@app.post("/api/publish")
def api_publish(entry:Entry):
    return myPublishFunc(entry.connection_string, entry.table_name, entry.text_path)
