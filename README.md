# Packard Power Rankings

This might be an approach to our fullstack project where we can containerize the frontend and backend. ~~I was talking to Dr. MacEvoy a little about the fullstack that uses MongoDB, and it might make more sense to switch to PostgreSQL since it can use both NoSQL and SQL databases and it works seamlessly with AWS. Here is a [template](https://github.com/PlatonovSerg/full-stack-fastapi/tree/master) that we could go off that, to me, would make the most sense and would give us the option to choose between SQL or NoSQL. Let me know what you guys think, but this swarm would give us that added boost with our development, we just need to talk to Dr. Basnet and Dr. Packard about it.~~ After talking to Dr. Basnet we will go with MongoDB instead for this and do it with NoSQL, looking at how PostgreSQL does there NoSQL it looks like a nightmare and is basically SQL. So, none of that we are sticking to the original plan. To get a good idea of how connecting the backend and database together you can read through this [article](https://testdriven.io/blog/fastapi-mongo/) and it give a pretty good idea of how things are structured. 


## Docker Compose Files and Commands

To start if you do not have Docker Desktop then you are going to need it to run the stuff I have below. You can find it at [Docker's](https://www.docker.com/products/docker-desktop/) website.

So far I have gotten the docker compose file setup so that we can containerize everything without having to install all the dependencies locally. It still is pretty bare bones but it should work, I will be making adjustments to help get it working a little bit better. 

Below are some commands that will need to be ran to get it working. The line below will automatically find the yaml file and start downloading the necessary files for you. 

`docker compose up -d --build`

Once it is completed you will see

```
 ✔ Container ppr-db-1        Running
 ✔ Container ppr-frontend-1  Started
 ✔ Container ppr-backend-1   Started 
```

Once the above command has been ran the first time, you only need to run the following command the next time just to bring the containers back online

`docker compose up -d`

That means it has created/started some containers for you. ~~The issue I am having thus far is where the container is loaded up to and all that. But I have been able to get things to work it just takes a little finessing to do it. That is what I will try and get working next.~~ Now all the containers load up just fine and should be easily accessed from a remote window.

From there you can run the specific container from the terminal as well with:

`docker exec -it ppr-backend-1 /bin/bash`

This above command is just a execute function with some other flags put into it. The ppr-backend-1 is the name of the container, you can also replace that with the <container_id>. If you run the below command it will show you that id number.

`docker ps`

```
CONTAINER ID   IMAGE          COMMAND                  CREATED             STATUS             PORTS                      NAMES
ad9d054cf4c4   ppr-frontend   "docker-entrypoint.s…"   57 seconds ago      Up 46 seconds      0.0.0.0:3000->3000/tcp     ppr-frontend-1
f5a75dffc217   ppr-backend    "uvicorn app.main:ap…"   57 seconds ago      Up 46 seconds      0.0.0.0:8000->8000/tcp     ppr-backend-1
8454ca613bbb   mongo:latest   "docker-entrypoint.s…"   About an hour ago   Up About an hour   0.0.0.0:27017->27017/tcp   ppr-db-1
```

The `/bin/bash` portion is just loading it into a bash style terminal, but that should be all that is necessary.

One thing to mention is that when this stack is created by docker compose you have to run the frontend or backend individually through the Remote window (the thing in the bottom right corner) and connect it to a running docker container. It will load up a separate window and all the dependencies will be loaded in as well.

Loading the remote connection will allow you to connect to the local server hosted from your computer and you can see updates live as you work, making development more seamless.

When you are finished working on something related to the project and want to turn docker off and stop all the containers you can run the following command

`docker compose down`

This command turns off all the active containers that are attached to this stack and removes any images that are still there, so docker is not just continuously running in the background.

Sometimes docker desktop needs to be refreshed and restarted to build the images. I noticed it will lag in the terminal and not do anything so if you try one of those things it will help get it going again.


## Local Testing

For local testing, the React frontend is set up to communicate with the FastAPI backend. Once the Docker containers are up, in VSCode, you can click on the `Open Remote Window` button and then `Attach to Runnning Container...` then choose `ppr-backend-1`. Open a terminal in the `ppr-backend-1` container and run the command `python api/main.py` to start the FastAPI local server.

You can now visit [localhost:8000](localhost:8000/docs) to view FastAPI's Swagger UI for backend testing and visit [localhost:3000](localhost:3000) to view React's locally hosted frontend for testing.


## FastAPI File Structure

I have also been working extensively on understanding the file structure for the backend portion of this program as well as some ideas about defining the structure of the database.


For the file structure we have this layout where I will explain in more detail in the backend [readme](https://github.com/Packard-Power-Rankings/ppr/blob/main/backend/api/README.md).

```
📦backend
 ┣ 📂api
 ┃ ┣ 📂external_services
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂routers
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂schemas
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂service
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂utils
 ┃ ┃ ┗ 📜__init__py
 ┃ ┣ 📜__init__.py
 ┃ ┣ 📜config.py
 ┃ ┣ 📜dependencies.py
 ┃ ┣ 📜main.py
 ┃ ┗ 📜README.md
 ┣ 📂tests
 ┃ ┣ 📜test_main.py
 ┃ ┗ 📜__init__.py
 ┣ 📜Dockerfile
 ┗ 📜requirements.txt
```


## MongoDB Information

For each of us I decided instead of using just one username and password for connecting to the Mongo client I have created a username and password for each person to be able to connect to that specific cluster.

The username and password needs to be stored in a .env file that is ignored from being pushed into github (if you do not have one please create one and set the variables to be used). 

Here is how I will have mine setup and so lets try and keep this the same with the variables throughout everyone's .env file so when we set the Mongo uri it won't cause issues on someone elses uri structure. 

```
MONGO_DB_NAME = "<mongo db name>"
MONGO_PASS = "<mongo pass>"
MONGO_USER = "<mongo username>"
MONGO_PORT = "<mongo port>"
```

For the Mongo URI it should be setup already through the docker-compose file which the docker-compose file should show this.

```
db:
.
.
environment:
      - MONGO_INITDB_DATABASE=${MONGO_DB_NAME}
      - MONGO_INITDB_ROOT_USERNAME=${MONGO_USER}
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASS}
    ports:
      - "${MONGO_PORT}:${MONGO_PORT}"

backend:
.
.
environment:
      - MONGO_URI=mongodb://${MONGO_USER}:${MONGO_PASS}@db:${MONGO_PORT}/${MONGO_DB_NAME}
```


## Git Branch Management and Best Practices

GitHub githooks and workflow adapted from [here](https://github.com/rambasnet/course-container).
