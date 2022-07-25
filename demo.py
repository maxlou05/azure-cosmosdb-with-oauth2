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


# Header is optional, using json parameter automatically changes it to application/json
# response = requests.post("https://ncydtestapi.azurewebsites.net/api/query", json=datatosend, headers=headers)
response = requests.post("http://localhost:8000/api/query", json=datatosend, headers=headers)
data = response.json()
print(response.status_code)
print(json.dumps(data, indent=True))


datatosend = {"connection_string":connection_string, "table_name":table_name, "partition_key":data["Query results"][1]["PartitionKey"], "row_key":data["Query results"][1]["RowKey"]}
# response = requests.post("https://ncydtestapi.azurewebsites.net/api/get", json=datatosend, headers=headers)
response = requests.post("http://localhost:8000/api/get", json=datatosend, headers=headers)
print(response.status_code)
print(json.dumps(response.json(), indent=True))


datatosend = {"connection_string":connection_string, "table_name":table_name, "partition_key":"", "row_key":"owisde984"}
# response = requests.post("https://ncydtestapi.azurewebsites.net/api/get", json=datatosend, headers=headers)
response = requests.post("http://localhost:8000/api/get", json=datatosend, headers=headers)
print(response.status_code)
print(json.dumps(response.json(), indent=True))


datatosend = {"connection_string":connection_string, "table_name":table_name}
# using data and files automatically sets the content type to multipart/form-data
# response = requests.post("https://ncydtestapi.azurewebsites.net/api/publish", json=datatosend)
response = requests.post("http://localhost:8000/api/publish", data=datatosend, files={"my_file":("my_file_name", open(text_path, "rb"))})
data = response.json()
print(response.status_code)
print(json.dumps(data, indent=True))


datatosend = {"connection_string":connection_string, "table_name":table_name, "partition_key":data["message"].split(" ")[5][1:-1], "row_key":data["message"].split(" ")[8][1:-1]}
# response = requests.post("https://ncydtestapi.azurewebsites.net/api/delete", json=datatosend, headers=headers)
response = requests.post("http://localhost:8000/api/delete", json=datatosend, headers=headers)
print(response.status_code)
print(json.dumps(response.json(), indent=True))
