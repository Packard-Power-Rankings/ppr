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
 ┃ ┃ ┃ ┣ 📜AdminPage.js    # Houses display logic for admin operations
 ┃ ┃ ┃ ┣ 📜CsvParser.js    # Parses CSV data
 ┃ ┃ ┃ ┣ 📜CsvTable.css    # Styles a table for CSV info
 ┃ ┃ ┃ ┣ 📜CsvTable.js     # Creates a table for CSV info
 ┃ ┃ ┃ ┣ 📜CsvUpload.js    # Connects to CSV upload logic and adjacent logic
 ┃ ┃ ┃ ┣ 📜DeleteForm.js   # Houses deletion functions
 ┃ ┃ ┃ ┣ 📜DeleteSeason.js # Connects to deletion logic
 ┃ ┃ ┃ ┣ 📜Login.js        # Connects to admin JWT authorization logic (required to be passed to all admin operations)
 ┃ ┃ ┃ ┣ 📜RunAlgorithm.js # Connects to RunAlgorithm logic
 ┃ ┃ ┃ ┣ 📜SportForm.js    # Houses sport_type, gender, level (required to be passed to all admin/user operations)
 ┃ ┃ ┃ ┗ 📜UpdateTeam.js   # Houses display logic for CSV upload and adjacent logic
 ┃ ┃ ┣ 📂user
 ┃ ┃ ┃ ┣ 📜TeamDetails.css # Styles a team's games table
 ┃ ┃ ┃ ┣ 📜TeamDetails.js  # Displays a team's games table
 ┃ ┃ ┃ ┣ 📜TeamsPage.css   # Styles Teams table
 ┃ ┃ ┃ ┗ 📜TeamsPage.js    # Displays Teams table
 ┃ ┃ ┣ 📜About.js          # Displays the About page
 ┃ ┃ ┣ 📜Home.js           # Displays the Home page
 ┃ ┃ ┣ 📜RankingTile.css   # Styles the Home page tiles
 ┃ ┃ ┣ 📜RankingTile.js    # Houses tile information
 ┃ ┃ ┗ 📜ThemeToggle.js    # Styles light and dark modes
 ┃ ┣ 📜App.js              # The entry point for the React app (links)
 ┃ ┣ 📜index.js            # The entry point for the React app (root)
 ┃ ┣ 📜Nav.css             # Styles the navigation bar
 ┃ ┗ 📜Styles.css          # Styles the theme (includes light and dark mode styles)
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

## Future Development Checklist
- [ ] Modify RankingTile.js routes in accordance with the appropriate MongoDB collection names for each sport (e.g. hs_football, college_football, etc.).
- [ ] Implement TeamDetails.js Z-score to be displayed for users and modify AdminPage.js (and create a new .js file to tie into it) to include access to the Z-score calculation route in the backend (admin_routes -> calc_z_scores).
- [ ] Implement Celery backend route (admin_routes -> task-status) in RunAlgorithm.js to display the progress of the task to the user (suggest also locking out the run algorithm button to prevent flooding the backend with requests).
- [ ] Implement backend deletion logic and accomodate in the frontend (DeleteSeason.js is connected to an empty route, DeleteForm will house various deletion operations).
