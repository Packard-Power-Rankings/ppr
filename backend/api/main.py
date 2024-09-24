#
# main.py
#
# The main entry point for running the FastAPI applicaton
# via Uvicorn server.
#

import uvicorn
from dependencies import app  # Importing the app from dependencies

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
