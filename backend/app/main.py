import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from logging import getLogger
from dotenv import load_dotenv

from .models import Entry, EntryResponse, EntriesResponse
from .constants import DB


load_dotenv()

# logger作成
logger = getLogger(__name__)

# MongoDB接続


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo = MongoClient(MONGO_URI)  # 起動時に1回だけ生成
    try:
        yield
    finally:
        app.state.mongo.close()  # 終了時にクローズ
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("[DEBUG] DATABASE_URLが未設定です。環境変数を設定してください。")
    exit(1)
MONGO_URI = DATABASE_URL

app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    print("access success")
    return {"message": "Hello World"}


@app.get("/entries")
async def get_entries(request: Request):
    client = request.app.state.mongo
    entries_collection = client[DB.DATABASE_NAME][DB.ENTRIES_COLLECTION]
    try:
        cursor = entries_collection.find({})
        entries = [
            Entry(**{k: v for k, v in doc.items() if k != "_id"}, id=str(doc["_id"])).model_dump()
            for doc in cursor
        ]
        return {"status": "success", "entries": entries}
    except PyMongoError as err:
        raise HTTPException(
            status_code=500, detail="failed to retrieve entries") from err


@app.post("/entries", response_model=EntryResponse)
async def add_entry(entry: Entry, request: Request) -> EntryResponse:
    client = request.app.state.mongo
    entries_collection = client[DB.DATABASE_NAME][DB.ENTRIES_COLLECTION]
    # dict化して挿入（JSON互換、Noneは除外）
    # dict化して挿入（JSON互換、Noneは除外、idは必ず除外）
    entry_dict = entry.model_dump(mode="json", exclude_none=True)
    if "id" in entry_dict:
        del entry_dict["id"]
    try:
        result = entries_collection.insert_one(entry_dict)
    except PyMongoError as err:
        raise HTTPException(
            status_code=500, detail="failed to insert entry") from err
    entry.id = str(result.inserted_id)
    return EntryResponse(status="success", entry=entry)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
