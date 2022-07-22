from fastapi import FastAPI, File, Form, Response, UploadFile, status
from pydantic import BaseModel
import table_api


app = FastAPI(debug=True)


class Query(BaseModel):
    connection_string : str
    table_name : str
    query : str | None
    fields : list[str] | None


class Entry(BaseModel):
    connection_string : str
    table_name : str


@app.get("/")
async def get_root():
    return {"Welcome": "to the FastAPI version"}


@app.post("/api/query", status_code=status.HTTP_200_OK)
async def api_query(query:Query):
    db = table_api.connect_to_db(query.connection_string)
    table = table_api.connect_to_table(db, query.table_name)
    query_results = list(table_api.query(table, query.query, query.fields))
    return {"Query results":query_results}


@app.post("/api/publish", status_code=status.HTTP_201_CREATED)
async def api_publish(connection_string:str = Form(), table_name:str = Form(), my_file:UploadFile = File()):
    content = await my_file.read()
    db = table_api.connect_to_db(connection_string)
    table = table_api.connect_to_table(db, table_name)
    entry = table_api.parse_bytes(content)
    table_api.upsert_entry(table, entry)
    return {"message":f"Successfully published deployment to table \"{table_name}\"!"}

