import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv

from .models import Entry, EntryResponse
from .constants import DB


load_dotenv()

# MongoDB接続
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("[DEBUG] DATABASE_URLが未設定です。環境変数を設定してください。")
    exit(1)
MONGO_URI = DATABASE_URL

app = FastAPI()


@app.get("/")
async def root():
    print("access success")
    return {"message": "Hello World"}


@app.post("/entries", response_model=EntryResponse, status_code=201)
async def add_entry(entry: Entry) -> EntryResponse:
    with MongoClient(MONGO_URI) as client:
        entries_collection = client[DB.DATABASE_NAME][DB.ENTRIES_COLLECTION]
        # dict化して挿入（JSON互換、Noneは除外）
        entry_dict = entry.model_dump(mode="json", exclude_none=True)
        entry_dict.pop("id", None)  # _id採番に任せる
        try:
            result = entries_collection.insert_one(entry_dict)
        except PyMongoError as err:
            raise HTTPException(status_code=500, detail="failed to insert entry") from err
        entry.id = str(result.inserted_id)
        return EntryResponse(status="success", entry=entry)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
