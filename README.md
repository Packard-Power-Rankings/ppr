# Packard Power Rankings

## About the Algorithm


The idea of the program is to model how a person would rank teams if they could process all the information and have no bias. The algorithm utilizes game scores and considers home-field advantage. When two teams play, one team should move up in power and the other down by the same amount based on their performances in relation to their current power ranking. In addition to the margin of victory, the algorithm considers the overall score in a game to create a more fair shift in a team’s power. For example, the difference between winning by 5 and 15 is much larger than the difference between winning by 35 and 45. In both games, the margin of victory is the same; however, 35 to 45 is considered a more even game than 5 to 15. It is also the case that a team could do worse than expected and still increase in power if they win. For instance, if the program predicts a team should win by 6 points and they only win by 3 points, they will still improve in power because they had a significant chance of losing.

Two teams that have recently played will affect the power scores of their other recent opponents. The effect on an opponent's power is influenced by the recency of the game. For example, if the #10 ranked college football team’s last opponent did much better than expected in their next game, the algorithm would increase the #10 team’s power by a fraction of their opponent’s change in power. If two teams with a wide power ranking play each other, and the team projected to lose ends up winning, there will be a much larger shift in rankings. Similarly, in the case that a highly favored team wins, both teams will see minimal change in their current power. For a team to move up in the rankings, they will need to perform well in their games, and their connected opponents will also have to perform well in their games.

At the start of a season, the initial rankings are simply the rankings from the end of the previous year. After scores are entered at the start of a new season, the rankings will fluctuate until enough data has been gathered and their appropriate ranking has been assigned. Finally, the algorithm is repeated several times over a season to achieve more accurate results.

## Score Predictions

While the primary purpose of this website is to rank teams, it also can predict the score of a hypothetical game played by two teams. The predictions are not meant to be considered definite scores, but decimal approximations of a hypothetical game outcome. This is analogous to guessing that a family has 2.4 children. Such a prediction cannot be correct, but an estimate of 2.4 might be a better estimate than 2, despite 2 having a chance of being exact.

## z-score



The z-score displayed on team pages measures the team’s performance in a game when considering the average performance across all games in a season and relies on the teams current power rankings. The score itself conveys how many standard deviations above or below the average game performance the team did in that game. A positive z-scores means that the game improved that team’s ranking and a negative one decreased it. The higher the z-score the more it helps a team. At least 75% of the time the z-score will be between -2 and 2, so if a z-score is greater than 2 or less than -2, that game was greatly impactful. After more games are played, these z-scores will change as the program will have more information and curve the z-scores up or down given the new information. With the z-scores, you can tell which games were the best and worst for a given team as viewed by the program. By looking at z-scores, we can decide which game was the best in the season.



## Docker Compose Files & Commands

To start if you do not have Docker Desktop then you are going to need it to run the stuff I have below. You can find it at [Docker's](https://www.docker.com/products/docker-desktop/) website.

So far I have gotten the docker compose file setup so that we can containerize everything without having to install all the dependencies locally. It still is pretty bare bones but it should work, I will be making adjustments to help get it working a little bit better. 

Below are some commands that will need to be ran to get it working. The line below will automatically find the yaml file and start downloading the necessary files for you. 

`docker compose up -d --build`

Once it is completed you will see

```
✔ Network ppr_app-network   Created
 ✔ Container ppr-db-1       Started
 ✔ Container ppr-backend-1  Started
 ✔ Container ppr-frontend-1 Started 
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


## Frontend & Local Testing

For local testing, the React frontend is set up to communicate with the FastAPI backend. Once the Docker containers are up, in VSCode, you can click on the `Open Remote Window` button and then `Attach to Runnning Container...` then choose `ppr-backend-1`. Open a terminal in the `ppr-backend-1` container and run the command `python api/main.py` to start the FastAPI local server.

You can now visit [localhost:8000](http://localhost:8000/docs) to view FastAPI's Swagger UI for backend testing and visit [localhost:3000](http://localhost:3000) to view React's locally hosted frontend for testing.

For the file structure we have this layout where I will explain in more detail in the frontend [readme](https://github.com/Packard-Power-Rankings/ppr/blob/main/frontend/README.md).

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


## Git Branch Management & Best Practices

GitHub githooks and workflow adapted from [here](https://github.com/rambasnet/course-container).
