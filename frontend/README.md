# React Frontend

## Layout

~~So far I have not spent as much time on this one yet. I have to restructure the Dockerfile so that when we load into this side of things that it loads into the proper file for this portion of the application.~~ 

## Testing
For local testing, launch the docker containers and navigate to localhost:3000 ([here](http://localhost:3000/)).

## File Structure [subject to change]

```
📦frontend
 ┣ 📂node_modules
 ┣ 📂public
 ┃ ┣ 📜index.html
 ┃ ┗ 📜R.ico
 ┣ 📂src
 ┃ ┣ 📂components
 ┃ ┃ ┣ 📜About.js
 ┃ ┃ ┣ 📜AdminPage.js
 ┃ ┃ ┣ 📜Home.css
 ┃ ┃ ┣ 📜Home.js
 ┃ ┃ ┣ 📜Login.js
 ┃ ┃ ┣ 📜RankingTile.css
 ┃ ┃ ┣ 📜RankingTile.js
 ┃ ┃ ┣ 📜SportForm.js
 ┃ ┃ ┗ 📜UploadForm.js
 ┃ ┣ 📜App.js
 ┃ ┣ 📜index.js
 ┃ ┗ 📜Nav.css
 ┣ 📜Dockerfile
 ┣ 📜dockerignore
 ┣ 📜gitignore
 ┣ 📜package-lock.json
 ┣ 📜package.json
 ┗ 📜README.md
```
