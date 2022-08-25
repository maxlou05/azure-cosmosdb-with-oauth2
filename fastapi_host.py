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
# This is used to 'sign' the token, so we can tell whether someone has tampered with it
# The signature (placed at the end of the token) is a hash? created from the contents of the token and the secret key
# So if someone changed the token contents, the signature should also change
# However, they don't know the secret key, so they will not be able to sign it properly
# When decoding a token, we use the secret key and 'sign' it, and see if the provided signature matches with the real signature
SECRET_KEY = os.environ["JWK"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

# User and role database info
USER_DB_CONN_STR = os.environ["CUSTOMCONNSTR_USER"]
USER_DB_NAME = os.environ["USER_DB_NAME"]
USER_CONTAINER_NAME = os.environ["USER_CONTAINER_NAME"]

# Table database info
DEFAULT_TABLE_CONN_STRING = os.environ["CUSTOMCONNSTR_TABLE"]
DEFAULT_TABLE_NAME = os.environ["TABLE_NAME"]

# We store hashed passwords in the database for security reasons:
# If an attacker ever got access to the database, they cannot steal the real plaintext password, as one cannot unhash somehting
# This is important especially because people use the same password for many different things
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


# The token object returned from the HTTP responses (ie Bearer sldfjs324ldfs6woei...)
class Token(BaseModel):
    access_token : str
    token_type : str


# What we are going to store in the token
# Remember, tokens are only encoded, anyone can see what's inside of the token
# Never put sensitive information in the token unless it has been encrypted before-hand
class TokenData(BaseModel):
    username : str


app = FastAPI()

# tokenURL is the path to take for getting a token (logging in)
# No need to add scopes, that is for situations when user decides what permissions they want to give third-party applications
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

# Set the hash functions to use the "bcrypt" algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Can use the demo_user_db here instead
def get_user(username:str):
    # The Microsoft pre-configured RBAC
    # cosmosdb_acc = CosmosClient("https://ncydsqlcosmos.documents.azure.com:443/", DefaultAzureCredential(exclude_interactive_browser_credential=False))
    cosmosdb_acc = CosmosClient.from_connection_string(USER_DB_CONN_STR)
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
        # The **dict means to pass all the key/value pairs in the dictionary as keyword arguments
        # So with a dict of d={"a":1, "b":2}, func(**d) == func(a=1, b=2)
        # It also automatically discards any keys that do not match a keyword argument
        return UserInDB(**results[0], username=results[0]["id"])


def get_hashed_password(plain_password:str):
    return pwd_context.hash(plain_password)


def verify_password(plain_password:str, hashed_password:str):
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


def authenticate_user(username:str, password:str):
    # See if this user exists in our database
    user = get_user(username)
    if user is None:
        return None
    # Check to see if they entered the correct password
    if not verify_password(password, user.hashed_password):
        return None
    return User(**user.dict())


# Depends means that this function needs to run the oauth2_scheme function (in this case a constructor function) before it can be executed
async def get_current_user(token:str = Depends(oauth2_scheme)):
    # It is standard to return the WWW-Authenticate header with value Bearer when using bearer tokens to authenticate, so users know to use Bearer tokens
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials", headers={"WWW-Authenticate" : "Bearer"})
    # Decoding the token for the user information
    try:
        payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=[ALGORITHM])
        # As per JWT convention/standards, 'sub' (aka subject) should be a unique identifier (as we did when creating the token)
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


# So depending on get_current_user means that after we get the current user, we can run this function and return their permissions
# This depending is for the async functionality, since we can go do other things that don't use current_user first
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
    # Set the 'sub' field as username, which is a unique identifier
    access_token = create_access_token(data={"sub":user.username}, expires_delta=access_token_expire)

    return {"access_token" : access_token, "token_type" : "Bearer"}


@app.post("/api/query", status_code=status.HTTP_200_OK)
async def api_query(query:Query, user_permissions:Permissions = Depends(get_permissions)):
    # Querying requires read permissions
    if(not user_permissions.read):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access denied: you do not have read permissions, please contact your system administrator")

    if query.connection_string is None:
        db = table_api.connect_to_db(DEFAULT_TABLE_CONN_STRING)
    else:
        db = table_api.connect_to_db(query.connection_string)
    if query.table_name is None:
        table = table_api.connect_to_table(db, DEFAULT_TABLE_NAME)
    else:
        table = table_api.connect_to_table(db, query.table_name)
    query_results = list(table_api.query(table, query.query, query.fields))
    return {"Query results" : query_results}


@app.post("/api/publish", status_code=status.HTTP_201_CREATED)
async def api_publish(connection_string:Optional[str] = Form(default=None), table_name:Optional[str] = Form(default=None), my_file:UploadFile = File(), user_permissions:Permissions = Depends(get_permissions)):
    # Publishing requires write permissions
    if(not user_permissions.write):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access denied: you do not have write permissions, please contact your system administrator")

    content = await my_file.read()
    if connection_string is None:
        db = table_api.connect_to_db(DEFAULT_TABLE_CONN_STRING)
    else:
        db = table_api.connect_to_db(connection_string)
    if table_name is None:
        table = table_api.connect_to_table(db, DEFAULT_TABLE_NAME)
    else:
        table = table_api.connect_to_table(db, table_name)
    entry = table_api.parse_bytes(content)
    table_api.upsert_entry(table, entry)
    return {"message" : "Successfully published deployment with PartitionKey \"{}\" and id \"{}\"!".format(entry["PartitionKey"], entry["RowKey"])}


@app.post("/api/get", status_code=status.HTTP_200_OK)
async def api_get(entity:Entity, user_permissions:Permissions = Depends(get_permissions)):
    # Getting requires read permissions
    if(not user_permissions.read):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access denied: you do not have read permissions, please contact your system administrator")

    if entity.connection_string is None:
        db = table_api.connect_to_db(DEFAULT_TABLE_CONN_STRING)
    else:
        db = table_api.connect_to_db(entity.connection_string)
    if entity.table_name is None:
        table = table_api.connect_to_table(db, DEFAULT_TABLE_NAME)
    else:
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

    if entity.connection_string is None:
        db = table_api.connect_to_db(DEFAULT_TABLE_CONN_STRING)
    else:
        db = table_api.connect_to_db(entity.connection_string)
    if entity.table_name is None:
        table = table_api.connect_to_table(db, DEFAULT_TABLE_NAME)
    else:
        table = table_api.connect_to_table(db, entity.table_name)
    table_api.delete_entry(table, id=entity.id, partition_key=entity.partition_key)
    return {"message" : f"Successfully deleted entry with PartitionKey \"{entity.partition_key}\" and id \"{entity.id}\"!"}
