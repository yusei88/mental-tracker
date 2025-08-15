import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv

from .models import Entry, EntryResponse, EntriesResponse
from .constants import DB

# 環境変数の読み込み
load_dotenv()

# 環境確認とDB接続URI取得
env = os.getenv("ENV", "development")
if env == "ci":
    # CI環境ではDB接続なし
    print("Running in CI mode - MongoDB connection skipped.")
    app = FastAPI(summary="KokoroNotoAPI_WithCI")
else:
    mongo_uri = os.getenv("MONGODB_URI")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.mongo = MongoClient(mongo_uri)  # 起動時に1回だけ生成
        try:
            yield
        finally:
            app.state.mongo.close()  # 終了時にクローズ

    app = FastAPI(lifespan=lifespan, summary="KokoroNotoAPI")


@app.get("/")
async def root():
    print("access success")
    return {"message": "Hello World"}


@app.get("/entries", response_model=EntriesResponse)
async def get_entries(request: Request) -> EntriesResponse:
    client = request.app.state.mongo
    entries_collection = client[DB.DATABASE_NAME][DB.ENTRIES_COLLECTION]
    try:
        cursor = entries_collection.find({})
        entries = [Entry(**doc) for doc in cursor]
        return EntriesResponse(status="success", entries=entries)
    except PyMongoError as err:
        raise HTTPException(
            status_code=500, detail="failed to retrieve entries") from err


@app.post("/entries", response_model=EntryResponse)
async def add_entry(entry: Entry, request: Request) -> EntryResponse:
    client = request.app.state.mongo
    entries_collection = client[DB.DATABASE_NAME][DB.ENTRIES_COLLECTION]
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
