from flask import Flask, jsonify, request
import table_api
import json

app = Flask(__name__)

def myQueryFunc(conn_str, table_name, query=None, fields=None):
    db = table_api.connect_to_db(conn_str)
    table = table_api.connect_to_table(db, table_name)
    query_results = list(table_api.query(table, query, fields))
    return jsonify({"Query results":query_results})


def myPublishFunc(conn_str, table_name, text_path):
    table_api.publish(text_path, conn_str, table_name)
    return jsonify({"message":f"Successfully published deployment to table \"{table_name}\"!"})


@app.get("/")
# AKA @app.route(path, methods=["GET"])
def index():
    return "Welcome to my app!"


@app.post("/query")
# AKA @app.route(path, methods=["POST"])
def query():
    data = None
    if(request.is_json):
        data = request.json
    else:
        data = request.form

    query = None
    fields = None

    try:
        query = data["query"]
    except:
        query = None
    try:
        fields = data["fields"]
    except:
        fields = None

    return myQueryFunc(data["connection_string"], data["table_name"], query, fields)


@app.post("/publish")
def publish_entry():
    data = None
    if(request.is_json):
        data = request.json
    else:
        data = request.form

    return myPublishFunc(data["connection_string"], data["table_name"], data["text_path"])


if(__name__ == "__main__"):
    app.run(debug=True)
