# FastAPI Layout

## File Structure
In the other read me I showed the details of how the files will be structured for the backend portion of this application.

```
📦backend
 ┣ 📂app
 ┃ ┣ 📂crud
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂external_services
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂models
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂routers
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂schemas
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂utils
 ┃ ┃ ┗ 📜__init__py
 ┃ ┣ 📜__init__.py
 ┃ ┣ 📜dependencies.py
 ┃ ┗ 📜main.py
 ┣ 📂tests
 ┃ ┗ 📜__init__.py
 ┣ 📜Dockerfile
 ┗ 📜requirements.txt
```
So far this is what I have:

* Crud File
    + This file contains all the crud operations: create, read, update, and delete hence the name of the file
    + All functionality with https requests will be handled through this file
* External Services
    + This is will hold models for handling specific services, such as emails and other things.
* Models
    + Models file will contain the files specific to creating the structure of the database and where things will go when requested
* Routers
    + This file will contain the files that will define routes and endpoints
* Schema
    + The schema file will be what holds all the Pydantic models which aid in defining the structure of received/sent details to the api
* Utils
    + This will contain certain files that might pertain to authorization and validation but I am unsure if this is needed yet
* dependencies.py
    + Sets the dependencies that are required by the router
* main.py
    + Used to initialize the FastAPI application

This is what I have got so far with this but we might have to change the structure of this to include an aws file that will be used to define a external service communication.