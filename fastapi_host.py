from datetime import datetime, timedelta
from typing import Optional, List, Dict
from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import BaseModel
from passlib.context import CryptContext
import table_api

# Token specifications and tools
# A 256-bit secret key
SECRET_KEY = "6985bb584d3db7340ede1b18bac6b44f7a5415b56ef5dabfd9352a775b090289"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15


fake_user_db = {
    "admin" : {
        "username" : "admin",
        "hashed_password" : "$2a$12$oHhJR57XnptaADwh0XZFs.d/wVUVVEwzjol.R2MwOlNyruzL2B4Fm", #adminpw
        "read" : True,
        "write" : True,
        "delete" : True,
        "email" : "myepicadminemail@email.com"
    },
    "standard_user" : {
        "username" : "standard_user",
        "hashed_password" : "$2a$12$wqp8f2TYuLMRBqV1o/5V5O7IFAHE9QgWNjkA4X6HLI6mSrYoDBf9K", #stdpw
        "read" : True,
        "write" : False,
        "delete" : False
    },
    "developer" : {
        "username" : "developer",
        "hashed_password" : "$2a$12$nodSMUpetRhqnSK3U1TKsu3IhkfRkGV78AvxxnOl0mTvS3jaIrqre", #devpw
        "read" : True,
        "write" : True,
        "delete" : False
    }
}


class Query(BaseModel):
    connection_string : str
    table_name : str
    query : Optional[str]
    fields : Optional[List[str]]


class Entity(BaseModel):
    connection_string : str
    table_name : str
    partition_key : str
    row_key : str


class Permissions(BaseModel):
    read : bool
    write : bool
    delete : bool


class User(Permissions):
    username : str
    email : Optional[str]


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


def get_user(db, username):
    if username in db:
        # Process our user info into a python-friendly Pydantic model/class
        # (this just saying the keyword arguments are in the dict, shortcut for specifying each key and value)
        # ie UserInDB(key1=db[username][key1], key2=db[username][key2], ...)
        return UserInDB(**db[username])
    return None


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
    # Add expiry info into our token (or just use to_encode[exp] = expire)
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def fake_decode_token(token):
    # Using Pydantic type casting, having extra keys doesn't matter!
    return UserInDB(**fake_user_db.get(token))
    # return User(**fake_user_db.get(token))


# Probably should use async if using real database which takes time to load data
def authenticate_user(fake_db, username, password):
    # See if this user exists in our database
    user = get_user(fake_db, username)
    if user is None:
        return False
    # Check to see if they entered the correct password
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(token:str = Depends(oauth2_scheme)):
    # It is standard to return the WWW-Authenticate header with value Bearer when using bearer tokens to authenticate
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials", headers={"WWW-Authenticate" : "Bearer"})
    # Decoding the token for the user information
    try:
        payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=[ALGORITHM])
        # As JWT convention/standards, "sub", or "subject" (as we did when creating the token) should be a unique identifier
        sub:str = payload.get("sub")
        if sub is None:
            raise credentials_exception
        token_data = TokenData(username=sub)
    # If there was an error decoding/invalid signature (and if token is expired, it automatically checks that)
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except JWTError:
        raise credentials_exception
    
    current_user = get_user(fake_user_db, username=token_data.username)
    if current_user is None:
        raise credentials_exception
    return current_user


async def get_current_user_email(current_user:User = Depends(get_current_user)):
    if current_user.email is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This user did not provide an email :(")
    return current_user


def get_permissions(current_user:User = Depends(get_current_user)):
    return Permissions(read=current_user.read, write=current_user.write, delete=current_user.delete)


@app.get("/")
def get_root():
    return {"Welcome" : "to the FastAPI version"}


@app.get("/secret_page")
def secret(user:User = Depends(get_current_user_email)):
    return {"Secret" : "You've found the secret!", "user" : user}


@app.post("/api/token", response_model=Token)
async def login(form_data:OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm)):
    # Retrieving user info from the database (logging in)
    user = authenticate_user(fake_user_db, form_data.username, form_data.password)
    # If user doesn't exist, or not authenticated
    if(user == False):
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
async def api_publish(connection_string:str = Form(), table_name:str = Form(), my_file:UploadFile = File(), user_permissions:Permissions = Depends(get_permissions)):
    # Publishing requires write permissions
    if(not user_permissions.write):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access denied: you do not have write permissions, please contact your system administrator")

    content = await my_file.read()
    db = table_api.connect_to_db(connection_string)
    table = table_api.connect_to_table(db, table_name)
    entry = table_api.parse_bytes(content)
    table_api.upsert_entry(table, entry)
    return {"message" : "Successfully published deployment with PartitionKey \"{}\" and RowKey \"{}\" to table \"{}\"!".format(entry["PartitionKey"], entry["RowKey"], table_name)}


@app.post("/api/get", status_code=status.HTTP_200_OK)
async def api_get(entity:Entity, user_permissions:Permissions = Depends(get_permissions)):
    # Getting requires read permissions
    if(not user_permissions.read):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access denied: you do not have read permissions, please contact your system administrator")

    db = table_api.connect_to_db(entity.connection_string)
    table = table_api.connect_to_table(db, entity.table_name)
    entry = table_api.get_entry(table, entity.partition_key, entity.row_key)
    if(entry is not None):
        return {"Entry" : entry}
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No entity found with the specified PartitionKey and RowKey")


@app.post("/api/delete", status_code=status.HTTP_200_OK)
async def api_delete(entity:Entity, user_permissions:Permissions = Depends(get_permissions)):
    # Deleting requires delete permissions
    if(not user_permissions.delete):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access denied: you do not have delete permissions, please contact your system administrator")

    db = table_api.connect_to_db(entity.connection_string)
    table = table_api.connect_to_table(db, entity.table_name)
    table_api.delete_entry(table, entity.partition_key, entity.row_key)
    return {"message" : f"Successfully deleted entry with PartitionKey \"{entity.partition_key}\" and RowKey \"{entity.row_key}\""}
