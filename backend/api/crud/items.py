from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    sport_type: str
    gender: str
    level: str
    team: str

@app.post("/items/")
async def create_item(item: Item):
    result = await app.mongodb["items"].insert_one(item.dict())
    if result:
        return {"id": str(result.inserted_id)}
    raise HTTPException(status_code=400, detail="Item not created")

@app.get("/items/{sport_type}")
async def get_item(sport_type: str):
    item = await app.mongodb["items"].find_one({"sport_type": sport_type})
    if item:
        return item
    raise HTTPException(status_code=404, detail="Item not found")
