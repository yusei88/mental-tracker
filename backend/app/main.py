import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId
from bson.errors import InvalidId
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

    try:
        result = entries_collection.insert_one(entry_dict)
    except PyMongoError as err:
        raise HTTPException(
            status_code=500, detail="failed to insert entry") from err
    entry.id = str(result.inserted_id)
    return EntryResponse(status="success", entry=entry)


@app.put("/entries", response_model=EntryResponse)
async def update_entry(entry: Entry, request: Request, id: str = Query(..., description="エントリーID")) -> EntryResponse:
    client = request.app.state.mongo
    entries_collection = client[DB.DATABASE_NAME][DB.ENTRIES_COLLECTION]
    
    # ObjectIdの妥当性をチェック
    try:
        object_id = ObjectId(id)
    except InvalidId as err:
        raise HTTPException(
            status_code=422, detail="Invalid entry ID format") from err
    
    # 更新データを準備（idを除外）
    entry_dict = entry.model_dump(mode="json", exclude_none=True)
    entry_dict.pop("id", None)  # IDは更新対象から除外
    
    try:
        # エントリーが存在するかチェックしてから更新
        result = entries_collection.replace_one(
            {"_id": object_id}, 
            entry_dict
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=404, detail="Entry not found")
        
        # 更新されたエントリーを返却用に設定
        entry.id = id
        return EntryResponse(status="success", entry=entry)
        
    except PyMongoError as err:
        raise HTTPException(
            status_code=500, detail="failed to update entry") from err


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
