import requests
import json

connection_string = "DefaultEndpointsProtocol=https;AccountName=ncydtabledb;AccountKey=BgxGmRqfcRSU79yTwXFaU8xY20vEcfD9kRpRvoeickozvdqhGutqz0Bq7qNSBpBPGinQLQSr2obU036m1Foq5w==;TableEndpoint=https://ncydtabledb.table.cosmos.azure.com:443/;"
table_name = "ncydconfigurationinfo"
query_string = "RowKey eq 'id'"
fields = ["PartitionKey", "RowKey"]
datatosend = {"connection_string":connection_string, "table_name":table_name, "query":query_string, "fields":fields}
# datatosend = {"connection_string":connection_string, "table_name":table_name}


response = requests.post("http://localhost:5000/query", json=datatosend)
data = response.json()
print(json.dumps(data, indent=True))

text_path = "C:/Users/mlou/Documents/cosmos practice/myTestDB/values.txt"
datatosend = {"connection_string":connection_string, "table_name":table_name, "text_path":text_path}
response = requests.post("http://localhost:5000/publish", json=datatosend)
print(json.dumps(response.json(), indent=True))
