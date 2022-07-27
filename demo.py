import requests
import json

connection_string = "DefaultEndpointsProtocol=https;AccountName=ncydtabledb;AccountKey=BgxGmRqfcRSU79yTwXFaU8xY20vEcfD9kRpRvoeickozvdqhGutqz0Bq7qNSBpBPGinQLQSr2obU036m1Foq5w==;TableEndpoint=https://ncydtabledb.table.cosmos.azure.com:443/;"
table_name = "ncydconfigurationinfo"
query_string = "RowKey eq 'id'"
fields = ["PartitionKey", "RowKey", "new_property"]
text_path = "./values.txt"
# text_path = "C:/Users/mlou/Documents/azure_app/values.txt"


payload = {"username":"admin", "password":"adminpw"}
# response = requests.post("https://ncydtestapi.azurewebsites.net/api/token", data=payload)
response = requests.post("http://localhost:8000/api/token", data=payload)
print(response.status_code)
data = response.json()
print(json.dumps(data, indent=True))


# To be authorized, need to provide "Authorization" header with a bearer token, as expected by the API
headers = {"Authorization":"{} {}".format(data["token_type"], data["access_token"])}
expired_token = {"Authorization":"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTY1ODg1ODU3Mn0.lpYitTIYax1lWmJ0NlkvxhMs2RmIVpKWDBqU__5hZDU"}


payload = {"connection_string":connection_string, "table_name":table_name, "query":query_string, "fields":fields}
# payload = {"connection_string":connection_string, "table_name":table_name}

# Authentication goes in the header
# response = requests.post("https://ncydtestapi.azurewebsites.net/api/query", json=payload, headers=expired_token)
response = requests.post("http://localhost:8000/api/query", json=payload, headers=expired_token)
print(response.status_code)
print(json.dumps(response.json(), indent=True))

# response = requests.post("https://ncydtestapi.azurewebsites.net/api/query", json=payload, headers=headers)
response = requests.post("http://localhost:8000/api/query", json=payload, headers=headers)
print(response.status_code)
data = response.json()
print(json.dumps(data, indent=True))


payload = {"connection_string":connection_string, "table_name":table_name, "partition_key":data["Query results"][1]["PartitionKey"], "row_key":data["Query results"][1]["RowKey"]}
# response = requests.post("https://ncydtestapi.azurewebsites.net/api/get", json=payload, headers=headers)
response = requests.post("http://localhost:8000/api/get", json=payload, headers=headers)
print(response.status_code)
print(json.dumps(response.json(), indent=True))


payload = {"connection_string":connection_string, "table_name":table_name, "partition_key":"", "row_key":"owisde984"}
# response = requests.post("https://ncydtestapi.azurewebsites.net/api/get", json=payload, headers=headers)
response = requests.post("http://localhost:8000/api/get", json=payload, headers=headers)
print(response.status_code)
print(json.dumps(response.json(), indent=True))


payload = {"connection_string":connection_string, "table_name":table_name}
# using data and files automatically sets the content type to multipart/form-data
# response = requests.post("https://ncydtestapi.azurewebsites.net/api/publish", data=payload, files={"my_file":("my_file_name", open(text_path, "rb"))}, headers=headers)
response = requests.post("http://localhost:8000/api/publish", data=payload, files={"my_file":("my_file_name", open(text_path, "rb"))}, headers=headers)
print(response.status_code)
data = response.json()
print(json.dumps(data, indent=True))


payload = {"connection_string":connection_string, "table_name":table_name, "partition_key":data["message"].split(" ")[5][1:-1], "row_key":data["message"].split(" ")[8][1:-1]}
# response = requests.post("https://ncydtestapi.azurewebsites.net/api/delete", json=payload, headers=headers)
response = requests.post("http://localhost:8000/api/delete", json=payload, headers=headers)
print(response.status_code)
print(json.dumps(response.json(), indent=True))
