# NCYD Deployment Information Automation Tool

Built a Flask app (`app.py` not complete, just for experimentation) and a FastAPI app (`fastapi_host.py`) as an API server.
The app is a microservice that can be hosted on the web (in this case it was hosted on Azure App Services).
The app includes simple OAuth2 password flow to authenticate users, and a users/credentials database is used to authorize and store roles/permissions.
In this case, a CosmosDB TableAPI database was used to store the information, while a CosmosDB core-SQL database was used to store the user credentials.

### Important endpoints
There is an auto-generated documentation (for the FastAPI app) at `/docs` and `/redocs`.
`/docs` is a interactive documentation where each API endpoint can be tested, while `/redocs` is just another view of the documentation (not interactive)

### Environment variables
The code is currently set to use a CosmosDB SQL database for storing user information, and a CosmosDB TableAPI database for storing the information.

- JWK: A 256-bit secret key for JWT token signing
- CUSTOMCONNSTR_USER: The 
