import requests
import json

connection_string = "DefaultEndpointsProtocol=https;AccountName=ncydtabledb;AccountKey=BgxGmRqfcRSU79yTwXFaU8xY20vEcfD9kRpRvoeickozvdqhGutqz0Bq7qNSBpBPGinQLQSr2obU036m1Foq5w==;TableEndpoint=https://ncydtabledb.table.cosmos.azure.com:443/;"
table_name = "ncydconfigurationinfo"
query_string = "RowKey eq 'id'"
fields = ["PartitionKey", "RowKey", "new_property"]
text_path = "./values.txt"
# text_path = "C:/Users/mlou/Documents/azure_app/values.txt"

headers = {"Content-Type": "application/json"}

datatosend = {"connection_string":connection_string, "table_name":table_name, "query":query_string, "fields":fields}
# datatosend = {"connection_string":connection_string, "table_name":table_name}


response = requests.put("https://ncydtestapi.azurewebsites.net/api/upload", files={"my_file":("my_file_name", open(text_path, "rb"))})
# response = requests.put("http://localhost:8000/api/upload", files={"my_file":("my_file_name", open(text_path, "rb"))})
print(response.status_code)
print(response.json())


# Header is optional, using json parameter automatically changes it to application/json
response = requests.post("https://ncydtestapi.azurewebsites.net/api/query", json=datatosend, headers=headers)
# response = requests.post("http://localhost:8000/api/query", json=datatosend, headers=headers)
data = response.json()
print(response.status_code)
print(json.dumps(data, indent=True))


datatosend = {"connection_string":connection_string, "table_name":table_name}
response = requests.post("https://ncydtestapi.azurewebsites.net/api/publish", json=datatosend)
# response = requests.post("http://localhost:8000/api/publish", json=datatosend)
print(response.status_code)
print(json.dumps(response.json(), indent=True))
