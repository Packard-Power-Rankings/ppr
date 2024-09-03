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


## FastAPI File Structure

I have also been working extensively on understanding the file structure for the backend portion of this program as well as some ideas about defining the structure of the database.


For the file structure we have this layout where I will explain in more detail in the backend [readme](/backend/app/README.md)

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