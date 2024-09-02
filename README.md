# Packard Power Rankings


This might be an approach to our fullstack project where we can containerize the frontend and backend. I was talking to Dr. MacEvoy a little about the fullstack that uses MongoDB, and it might make more sense to switch to PostgreSQL since it can use both NoSQL and SQL databases and it works seamlessly with AWS. Here is a [template](https://github.com/PlatonovSerg/full-stack-fastapi/tree/master) that we could go off that, to me, would make the most sense and would give us the option to choose between SQL or NoSQL. Let me know what you guys think, but this swarm would give us that added boost with our development, we just need to talk to Dr. Basnet and Dr. Packard about it.


So far I have gotten the docker compose file setup so that we can containerize everything without having to install all the dependencies locally. It still is pretty bare bones but it should work, I will be making adjustments to help get it working a little bit better. 


Below are some commands that will need to be ran to get it working. The line below will automatically find the yaml file and start downloading the necessary files for you. 

`docker compose up -d --build`

Once it is completed you will see

```
[+] Running 4/4
✔ Network ppr_default       Created
✔ Container ppr-frontend-1  Started
✔ Container ppr-db-1        Started
✔ Container ppr-backend-1   Started
```

That means it has created/started some containers for you. This issue I am having thus far is where the container is loaded up to and all that. But I have been able to get things to work it just takes a little finessing to do it. That is what I will try and get working next.


I have also been working extensively on understanding the file structure for the backend portion of this program as well as some ideas about defining the structure of the database.


for the file structure we have this layout where I will explain in more detail in the backend [readme](/backend/app/README.md)

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