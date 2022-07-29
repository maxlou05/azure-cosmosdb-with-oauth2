import requests
import json

query_string = "RowKey eq 'id' or new_property gt 100"
fields = ["PartitionKey", "RowKey", "new_property"]
text_path = "./values.txt"

# Demo users
payload = {"username":"admin", "password":"adminpw"}
# payload = {"username":"dev", "password":"devpw"}
# payload = {"username":"standard_user", "password":"stdpw"}


print("----------Getting token------------")
# response = requests.post("https://ncydtestapi.azurewebsites.net/api/token", data=payload)
response = requests.post("http://localhost:8000/api/token", data=payload)
print(response.status_code)
data = response.json()
print(json.dumps(data, indent=True))


# To be authorized, need to provide "Authorization" header with a bearer token, as expected by the API
headers = {"Authorization":"{} {}".format(data["token_type"], data["access_token"])}
expired_token = {"Authorization":"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTY1ODg1ODU3Mn0.lpYitTIYax1lWmJ0NlkvxhMs2RmIVpKWDBqU__5hZDU"}


print("--------------Using expired token----------------")
payload = {"query":query_string, "fields":fields}

# Authentication goes in the header
# response = requests.post("https://ncydtestapi.azurewebsites.net/api/query", json=payload, headers=expired_token)
response = requests.post("http://localhost:8000/api/query", json=payload, headers=expired_token)
print(response.status_code)
print(json.dumps(response.json(), indent=True))


print("--------------Querying-------------")
# response = requests.post("https://ncydtestapi.azurewebsites.net/api/query", json=payload, headers=headers)
response = requests.post("http://localhost:8000/api/query", json=payload, headers=headers)
print(response.status_code)
data = response.json()
print(json.dumps(data, indent=True))


print("---------------Getting item 4 of query--------------")
payload = {"partition_key":data["Query results"][3]["PartitionKey"], "id":data["Query results"][3]["RowKey"]}
# response = requests.post("https://ncydtestapi.azurewebsites.net/api/get", json=payload, headers=headers)
response = requests.post("http://localhost:8000/api/get", json=payload, headers=headers)
print(response.status_code)
print(json.dumps(response.json(), indent=True))


print("--------------Getting inexistant item----------------")
payload = {"id":"owisde984"}
# response = requests.post("https://ncydtestapi.azurewebsites.net/api/get", json=payload, headers=headers)
response = requests.post("http://localhost:8000/api/get", json=payload, headers=headers)
print(response.status_code)
print(json.dumps(response.json(), indent=True))


print("--------------Publishing deployment info-------------")
payload = {}
# using data and files automatically sets the content type to multipart/form-data
# response = requests.post("https://ncydtestapi.azurewebsites.net/api/publish", data=payload, files={"my_file":("my_file_name", open(text_path, "rb"))}, headers=headers)
response = requests.post("http://localhost:8000/api/publish", data=payload, files={"my_file":("my_file_name", open(text_path, "rb"))}, headers=headers)
print(response.status_code)
data = response.json()
print(json.dumps(data, indent=True))


print("--------------Deleting item that was just published------------")
if(response.status_code == 201):
    payload = {"partition_key":data["message"].split(" ")[5][1:-1], "id":data["message"].split(" ")[8][1:-2]}
else:
    payload = {"id":"some_id"}
# response = requests.post("https://ncydtestapi.azurewebsites.net/api/delete", json=payload, headers=headers)
response = requests.post("http://localhost:8000/api/delete", json=payload, headers=headers)
print(response.status_code)
print(json.dumps(response.json(), indent=True))
