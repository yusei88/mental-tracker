import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from dotenv import load_dotenv

from .models import Entry, EntryResponse
from .constants import DB

load_dotenv()

# MongoDB接続
MONGO_URI = os.getenv("DATABASE_URL")

app = FastAPI()


@app.get("/")
async def root():
    print("access success")
    return {"message": "Hello World"}


@app.post("/entries")
async def add_entry(entry: Entry):
    with MongoClient(MONGO_URI) as client:
        entries_collection = client[DB.DATABASE_NAME][DB.ENTRIES_COLLECTION]
        # model_dump_jsonでdateをISO文字列化し、dict化して挿入
        entry_dict = json.loads(entry.model_dump_json())
        result = entries_collection.insert_one(entry_dict)
        entry.id = str(result.inserted_id)
        return EntryResponse(status="success", entry=entry)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
