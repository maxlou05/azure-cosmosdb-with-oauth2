# NCYD Deployment Information Automation Tool

Built a Flask app (`app.py` not complete, just for experimentation) and a FastAPI app (`fastapi_host.py`) as an API server.
The app is a microservice that can be hosted on the web (in this case it was hosted on Azure App Services).
The app includes a simple OAuth 2.0 password grant to authenticate users, and a users/credentials database is used to store user credentials and roles/permissions.
In this case, a CosmosDB TableAPI database was used to store the information, while a CosmosDB core-SQL database was used to store the user credentials.

## Important endpoints
There is an auto-generated documentation (for the FastAPI app) at `/docs` and `/redocs`.
`/docs` is a interactive documentation where each API endpoint can be tested, while `/redocs` is just another view of the documentation (not interactive)

## Environment variables
The code is currently set to use a CosmosDB SQL database for storing user information, and a CosmosDB TableAPI database for storing the information.
The CLI is currently configured to use a default table name.

- JWK: A 256-bit secret key for JWT token signing
- CUSTOMCONNSTR_USER: The connection string to the CosmosDB SQL database (for the user information)
- USER_DB_NAME: The name of the CosmosDB SQL database (for the user information)
- USER_CONTAINER_NAME: The name of the container which contains the user information (for the CosmosDB SQL database)
- CUSTOMCONNSTR_TABLE: The connection string to the CosmosDB TableAPI database (for storing deployment information)
- TABLE_NAME: The default table name to use for the CosmosDB TableAPI database (for storing deployment information)
