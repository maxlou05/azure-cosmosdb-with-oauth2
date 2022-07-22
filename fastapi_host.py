from typing import Optional, List, Dict
from fastapi import FastAPI, File, Form, Response, UploadFile, status
from pydantic import BaseModel
import table_api

app = FastAPI(debug=True)

cached_file = None


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


class NewEntry(BaseModel):
    connection_string : str
    table_name : str


def myQueryFunc(conn_str, table_name, query=None, fields=None):
    db = table_api.connect_to_db(conn_str)
    table = table_api.connect_to_table(db, table_name)
    query_results = list(table_api.query(table, query, fields))
    return {"Query results":query_results}


def myPublishFunc(conn_str, table_name, entry):
    db = table_api.connect_to_db(conn_str)
    table = table_api.connect_to_table(db, table_name)
    table_api.upsert_entry(table, entry)
    return {"message":f"Successfully published deployment to table \"{table_name}\"!"}


@app.get("/")
def get_root():
    return {"Welcome": "to the FastAPI version"}


@app.post("/api/query", status_code=status.HTTP_200_OK)
def api_query(query:Query):
    return myQueryFunc(query.connection_string, query.table_name, query.query, query.fields)


@app.post("/api/publish", status_code=status.HTTP_201_CREATED)
def api_publish(entry:NewEntry, response:Response):
    global cached_file
    if cached_file is not None:
        success_message = myPublishFunc(entry.connection_string, entry.table_name, cached_file)
        cached_file = None
        return success_message
    response.status_code = status.HTTP_400_BAD_REQUEST
    return {"detail": "Please upload a file containing deployment information first"}


@app.put("/api/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(my_file:UploadFile):
    global cached_file
    print(my_file.filename)
    print("uploadV1!!!!")
    content = await my_file.read()
    cached_file = table_api.parse_bytes(content)
    return {"message": "Successfully uploaded and parsed deployment information"}
