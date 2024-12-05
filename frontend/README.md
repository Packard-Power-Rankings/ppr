# React Frontend

## Layout

~~So far I have not spent as much time on this one yet. I have to restructure the Dockerfile so that when we load into this side of things that it loads into the proper file for this portion of the application.~~ 

## Testing
For local testing, launch the docker containers and navigate to localhost:3000 ([here](http://localhost:3000/)).

## File Structure

```
📦frontend
 ┣ 📂node_modules
 ┣ 📂public
 ┃ ┣ 📜index.html
 ┃ ┣ 📜manifest.json
 ┃ ┗ 📜R.ico
 ┣ 📂src
 ┃ ┣ 📂components
 ┃ ┃ ┣ 📂admin
 ┃ ┃ ┃ ┣ 📜AdminPage.js
 ┃ ┃ ┃ ┣ 📜CsvParser.js
 ┃ ┃ ┃ ┣ 📜CsvTable.css
 ┃ ┃ ┃ ┣ 📜CsvTable.js
 ┃ ┃ ┃ ┣ 📜CsvUpload.js
 ┃ ┃ ┃ ┣ 📜DeleteForm.js
 ┃ ┃ ┃ ┣ 📜DeleteSeason.js
 ┃ ┃ ┃ ┣ 📜Login.js
 ┃ ┃ ┃ ┣ 📜RunAlgorithm.js
 ┃ ┃ ┃ ┣ 📜SportForm.js
 ┃ ┃ ┃ ┗ 📜UpdateTeam.js
 ┃ ┃ ┣ 📂user
 ┃ ┃ ┃ ┣ 📜TeamDetails.css
 ┃ ┃ ┃ ┣ 📜TeamDetails.js
 ┃ ┃ ┃ ┣ 📜TeamsPage.css
 ┃ ┃ ┃ ┗ 📜TeamsPage.js
 ┃ ┃ ┣ 📜About.js
 ┃ ┃ ┣ 📜Home.js
 ┃ ┃ ┣ 📜RankingTile.css
 ┃ ┃ ┣ 📜RankingTile.js
 ┃ ┃ ┗ 📜ThemeToggle.js
 ┃ ┣ 📜App.js
 ┃ ┣ 📜index.js
 ┃ ┣ 📜Nav.css
 ┃ ┗ 📜Styles.css
 ┣ 📂tests
 ┃ ┣ 📜test_teams.csv
 ┃ ┗ 📜test_teams_empty.csv
 ┣ 📜Dockerfile
 ┣ 📜dockerignore
 ┣ 📜gitignore
 ┣ 📜package-lock.json
 ┣ 📜package.json
 ┗ 📜README.md
```
