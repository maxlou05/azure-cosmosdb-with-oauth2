from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import BaseModel
from passlib.context import CryptContext
import table_api
import os

# Token specifications and tools
# A 256-bit secret key (32 digit hexadecimal, or 64 letters total)
SECRET_KEY = os.environ["JWK"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

# User and role database info
# USER_DB_CONN_STR = os.environ["CUSTOMCONNSTR_USER"]
USER_DB_NAME = os.environ["USER_DB_NAME"]
USER_CONTAINER_NAME = os.environ["USER_CONTAINER_NAME"]


# demo_user_db = {
#     "admin" : {
#         "id" : "admin",
#         "hashed_password" : "$2a$12$oHhJR57XnptaADwh0XZFs.d/wVUVVEwzjol.R2MwOlNyruzL2B4Fm", #adminpw
#         "permissions" : {
#             "read" : True,
#             "write" : True,
#             "delete" : True},
#         "email" : "myadmin@email.com"
#     },
#     "standard_user" : {
#         "id" : "standard_user",
#         "hashed_password" : "$2a$12$wqp8f2TYuLMRBqV1o/5V5O7IFAHE9QgWNjkA4X6HLI6mSrYoDBf9K", #stdpw
#         "permissions" : {
#             "read" : True,
#             "write" : False,
#             "delete" : False},
#     },
#     "dev" : {
#         "id" : "dev",
#         "hashed_password" : "$2a$12$nodSMUpetRhqnSK3U1TKsu3IhkfRkGV78AvxxnOl0mTvS3jaIrqre", #devpw
#         "permissions" : {
#             "read" : True,
#             "write" : True,
#             "delete" : False},
#     }
# }


class Query(BaseModel):
    connection_string : Optional[str]
    table_name : Optional[str]
    query : Optional[str]
    fields : Optional[List[str]]


class Entity(BaseModel):
    connection_string : Optional[str]
    table_name : Optional[str]
    partition_key : Optional[str]
    id : str


class Permissions(BaseModel):
    read : bool
    write : bool
    delete : bool


class User(BaseModel):
    username : str
    email : Optional[str]
    permissions : Permissions


class UserInDB(User):
    hashed_password : str


# The token object returned in the HTTP responses (ie Bearer sldfjs324ldfs6woei...)
class Token(BaseModel):
    access_token : str
    token_type : str


# What we are going to store in the token
class TokenData(BaseModel):
    username : str


app = FastAPI()

# tokenURL is the path to take for getting a token (logging in)
# No need to add scopes, that is for situations when user decides what permissions they want to give third-party applications
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

# Set the hash functions to use the "bcrypt" algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user(username):
    cosmosdb_acc = CosmosClient("https://ncydsqlcosmos.documents.azure.com:443/", DefaultAzureCredential(exclude_interactive_browser_credential=False))
    # cosmosdb_acc = CosmosClient.from_connection_string(USER_DB_CONN_STR)
    userdb = cosmosdb_acc.get_database_client(USER_DB_NAME)
    container = userdb.get_container_client(USER_CONTAINER_NAME)

    # Query for our user
    results = list(container.query_items(query="SELECT * FROM c WHERE c.id = @username",
        parameters=[dict(name="@username", value=username)],
        enable_cross_partition_query=True
    ))
    if(len(results) == 0):
        return None
    else:
        return UserInDB(**results[0], username=results[0]["id"])


def get_hashed_password(plain_password):
    return pwd_context.hash(plain_password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data:Dict, expires_delta:Optional[timedelta] = None):
    # A JWT is an encoded representation of some JSON object, anyone can decode it, but it has a signature
    # This signature is based on the SECRET_KEY, and is used to verify you made the token
    to_encode = data.copy()
    if expires_delta is not None:
        expire = datetime.utcnow() + expires_delta
    else:
        # If no specified token expiry date (for now, set it to 15 minutes for security reasons)
        expire = datetime.utcnow() + timedelta(minutes=15)
    # Add expiry info into our token (ie to_encode["exp"] = expire)
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Probably should use async if using real database which takes time to load data
def authenticate_user(username, password):
    # See if this user exists in our database
    user = get_user(username)
    if user is None:
        return None
    # Check to see if they entered the correct password
    if not verify_password(password, user.hashed_password):
        return None
    return User(**user.dict())


async def get_current_user(token:str = Depends(oauth2_scheme)):
    # It is standard to return the WWW-Authenticate header with value Bearer when using bearer tokens to authenticate
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials", headers={"WWW-Authenticate" : "Bearer"})
    # Decoding the token for the user information
    try:
        payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=[ALGORITHM])
        # As per JWT convention/standards, "sub" (aka subject) should be a unique identifier (as we did when creating the token)
        sub:str = payload.get("sub")
        if sub is None:
            raise credentials_exception
        token_data = TokenData(username=sub)
    # If there was an error decoding/invalid signature (and if token is expired, it automatically checks that)
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except JWTError:
        raise credentials_exception
    
    current_user = User(**get_user(token_data.username).dict())
    if current_user is None:
        raise credentials_exception
    return current_user


def get_permissions(current_user:User = Depends(get_current_user)):
    return current_user.permissions


@app.get("/")
def get_root():
    return {"Welcome" : "to the FastAPI version"}


@app.get("/user-info", response_model=User)
def get_info(user:User = Depends(get_current_user)):
    return user


@app.post("/api/token", response_model=Token)
async def login(form_data:OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm)):
    # Retrieving user info from the database (logging in)
    user = authenticate_user(form_data.username, form_data.password)
    # If user doesn't exist, or not authenticated
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    
    # Now that the user has logged in, create a token for them
    access_token_expire = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub":user.username}, expires_delta=access_token_expire)

    return {"access_token" : access_token, "token_type" : "Bearer"}


@app.post("/api/query", status_code=status.HTTP_200_OK)
async def api_query(query:Query, user_permissions:Permissions = Depends(get_permissions)):
    # Querying requires read permissions
    if(not user_permissions.read):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access denied: you do not have read permissions, please contact your system administrator")

    db = table_api.connect_to_db(query.connection_string)
    table = table_api.connect_to_table(db, query.table_name)
    query_results = list(table_api.query(table, query.query, query.fields))
    return {"Query results" : query_results}


@app.post("/api/publish", status_code=status.HTTP_201_CREATED)
async def api_publish(connection_string:Optional[str] = Form(default=None), table_name:Optional[str] = Form(default=None), my_file:UploadFile = File(), user_permissions:Permissions = Depends(get_permissions)):
    # Publishing requires write permissions
    if(not user_permissions.write):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access denied: you do not have write permissions, please contact your system administrator")

    content = await my_file.read()
    db = table_api.connect_to_db(connection_string)
    table = table_api.connect_to_table(db, table_name)
    entry = table_api.parse_bytes(content)
    table_api.upsert_entry(table, entry)
    return {"message" : "Successfully published deployment with PartitionKey \"{}\" and id \"{}\"!".format(entry["PartitionKey"], entry["RowKey"])}


@app.post("/api/get", status_code=status.HTTP_200_OK)
async def api_get(entity:Entity, user_permissions:Permissions = Depends(get_permissions)):
    # Getting requires read permissions
    if(not user_permissions.read):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access denied: you do not have read permissions, please contact your system administrator")

    db = table_api.connect_to_db(entity.connection_string)
    table = table_api.connect_to_table(db, entity.table_name)
    entry = table_api.get_entry(table, id=entity.id, partition_key=entity.partition_key)
    if(entry is not None):
        return {"Entry" : entry}
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No entity found with the specified PartitionKey and id")


@app.post("/api/delete", status_code=status.HTTP_200_OK)
async def api_delete(entity:Entity, user_permissions:Permissions = Depends(get_permissions)):
    # Deleting requires delete permissions
    if(not user_permissions.delete):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access denied: you do not have delete permissions, please contact your system administrator")

    db = table_api.connect_to_db(entity.connection_string)
    table = table_api.connect_to_table(db, entity.table_name)
    table_api.delete_entry(table, id=entity.id, partition_key=entity.partition_key)
    return {"message" : f"Successfully deleted entry with PartitionKey \"{entity.partition_key}\" and id \"{entity.id}\"!"}
