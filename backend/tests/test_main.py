import pytest
from datetime import date
import importlib
import sys

"""
FastAPIのエンドポイントをテストするためのクラス
"""


class TestMainApi:
    # 定数
    DUMMY_ID = "507f1f77bcf86cd799439011"  # 有効なObjectID形式
    FIXED_DATE = date(2025, 8, 14)

    def dummy_entry_as_doc(self):
        """dummy_entryをMongoDB document形式に変換"""
        from app.models import Entry
        dummy = Entry(
            id=self.DUMMY_ID,
            record_date=self.FIXED_DATE,
            mood_score=4,
            sleep_hours=6.5,
            memo="今日はよく眠れた"
        )
        return dummy.to_mongo_dict()

    @pytest.fixture
    def dummy_entry(self):
        from app.models import Entry
        return Entry(
            id=self.DUMMY_ID,
            record_date=self.FIXED_DATE,
            mood_score=4,
            sleep_hours=6.5,
            memo="今日はよく眠れた"
        )

    @pytest.fixture
    def client(self, monkeypatch):
        return self._create_client("normal")

    def _create_client(self, mock_type="normal"):
        from fastapi.testclient import TestClient
        from app.main import app

        class MockInsertOneResult:
            @property
            def inserted_id(self):
                return TestMainApi.DUMMY_ID

        # ダミーデータを生成
        test_instance = self

        class MockCollection:
            def __init__(self, mock_type="normal"):
                self.mock_type = mock_type

            def insert_one(self, entry):
                if self.mock_type == "error":
                    from pymongo.errors import PyMongoError
                    raise PyMongoError("Database connection failed")
                else:
                    # 実際のDB挿入は不要。inserted_idのみ返す
                    return MockInsertOneResult()

            def find(self, query):
                if self.mock_type == "empty":
                    return []
                elif self.mock_type == "error":
                    from pymongo.errors import PyMongoError
                    raise PyMongoError("Database connection failed")
                else:
                    return [test_instance.dummy_entry_as_doc()]

            def find_one(self, query):
                if self.mock_type == "error":
                    from pymongo.errors import PyMongoError
                    raise PyMongoError("Database connection failed")
                elif self.mock_type == "not_found":
                    return None
                else:
                    return test_instance.dummy_entry_as_doc()

            def delete_one(self, query):
                if self.mock_type == "error":
                    from pymongo.errors import PyMongoError
                    raise PyMongoError("Database connection failed")
                else:
                    class MockDeleteResult:
                        @property
                        def deleted_count(self):
                            return 1
                    return MockDeleteResult()

        class MockDB:
            def __init__(self, mock_type="normal"):
                self.mock_type = mock_type

            def __getitem__(self, name):
                return MockCollection(self.mock_type)

        class MockClient:
            def __init__(self, mock_type="normal"):
                self.mock_type = mock_type

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

            def __getitem__(self, name):
                return MockDB(self.mock_type)

        # lifespan利用のため、app起動前にstate.mongoへ直接MockClientをセット
        app.state.mongo = MockClient(mock_type)
        return TestClient(app)

    # サンプルテスト
    """
    Feature: サンプル用のルートエンドポイントAPI
        Scenario: ルートエンドポイントにGetリクエストを実行すると成功のレスポンスを受け取る
            Given: 実行可能なAPIクライアントがある
            When:  ルートエンドポイントにGetリクエストを実行する
            Then:  レスポンスのステータスコードは200である
            And:   レスポンスの'message'に'Hello World'含まれる
    """

    def test_read_main(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}

    # エントリー追加APIの正常系テスト
    """
    Feature: エントリー追加API
        Scenario: エントリーの追加に成功する
            Given: 実行可能なAPIクライアントがある
            When:  有効なエントリーデータで'/entries'にPOSTする
            Then:  レスポンスのステータスコードは200である
            And:   レスポンスボディのキー'status'のバリューに'success'が含まれる
            And:   レスポンスボディのキー'entry'のバリューにエントリー情報が含まれる
    """

    def test_add_entry_success(self, client, dummy_entry):
        # dummy_entryをdict化してPOST
        entry_dict = dummy_entry.model_dump()
        # idはAPIのPOSTでは不要なので除外
        entry_dict.pop("id", None)
        # dateはISO文字列に変換
        entry_dict["record_date"] = dummy_entry.record_date.isoformat()
        response = client.post("/entries", json=entry_dict)
        assert response.status_code == 200
        resp_json = response.json()
        assert resp_json.get("status") == "success"
        # entry内容を厳密に検証
        entry = resp_json.get("entry")
        assert entry is not None
        assert entry["id"] == self.DUMMY_ID
        assert entry["record_date"] == self.FIXED_DATE.isoformat()
        assert entry["mood_score"] == dummy_entry.mood_score
        assert entry["sleep_hours"] == dummy_entry.sleep_hours
        assert entry["memo"] == dummy_entry.memo

    # エントリー追加APIの準正常系/異常系・バリデーション系テスト
    """
    Feature: エントリー追加API
        Scenario: memoが空文字でも登録できる
            Given: 実行可能なAPIクライアントがある
            When:  memoが空文字で'/entries'にPOSTする
            Then:  レスポンスのステータスコードは200である
            And:   レスポンスボディのキー'entry'のmemoが空文字である
    """

    def test_add_entry_empty_memo(self, client, dummy_entry):
        entry_dict = dummy_entry.model_dump()
        entry_dict.pop("id", None)
        entry_dict["record_date"] = dummy_entry.record_date.isoformat()
        entry_dict["memo"] = ""
        response = client.post("/entries", json=entry_dict)
        assert response.status_code == 200
        resp_json = response.json()
        entry = resp_json.get("entry")
        assert entry is not None
        assert entry["memo"] == ""

    """
    Feature: エントリー追加API
        Scenario: 必須項目record_dateが不足している場合は422エラーとなる
            Given: 実行可能なAPIクライアントがある
            When:  必須項目record_dateが欠落したデータで'/entries'にPOSTする
            Then:  レスポンスのステータスコードは422である
            And:   レスポンスボディにバリデーションエラーが含まれる
    """

    def test_add_entry_missing_date(self, client, dummy_entry):
        entry_dict = dummy_entry.model_dump()
        entry_dict.pop("id", None)
        entry_dict["record_date"] = dummy_entry.record_date.isoformat()
        entry_dict.pop("record_date", None)
        response = client.post("/entries", json=entry_dict)
        assert response.status_code == 422
        resp_json = response.json()
        assert "error" in resp_json.get(
            "detail", "") or "record_date" in str(resp_json)

    """
    Feature: エントリー追加API
        Scenario: 必須項目mood_scoreが不足している場合は422エラーとなる
            Given: 実行可能なAPIクライアントがある
            When:  必須項目mood_scoreが欠落したデータで'/entries'にPOSTする
            Then:  レスポンスのステータスコードは422である
            And:   レスポンスボディにバリデーションエラーが含まれる
    """

    def test_add_entry_missing_mood_score(self, client, dummy_entry):
        entry_dict = dummy_entry.model_dump()
        entry_dict.pop("id", None)
        entry_dict["record_date"] = dummy_entry.record_date.isoformat()
        entry_dict.pop("mood_score", None)
        response = client.post("/entries", json=entry_dict)
        assert response.status_code == 422
        resp_json = response.json()
        assert "error" in resp_json.get(
            "detail", "") or "mood_score" in str(resp_json)

    """
    Feature: エントリー追加API
        Scenario: 必須項目sleep_hoursが不足している場合は422エラーとなる
            Given: 実行可能なAPIクライアントがある
            When:  必須項目sleep_hoursが欠落したデータで'/entries'にPOSTする
            Then:  レスポンスのステータスコードは422である
            And:   レスポンスボディにバリデーションエラーが含まれる
    """

    def test_add_entry_missing_sleep_hours(self, client, dummy_entry):
        entry_dict = dummy_entry.model_dump()
        entry_dict.pop("id", None)
        entry_dict["record_date"] = dummy_entry.record_date.isoformat()
        entry_dict.pop("sleep_hours", None)
        response = client.post("/entries", json=entry_dict)
        assert response.status_code == 422
        resp_json = response.json()
        assert "error" in resp_json.get(
            "detail", "") or "sleep_hours" in str(resp_json)

    """
    Feature: エントリー追加API
        Scenario: mood_scoreが負の数の場合はバリデーションエラーとなる
            Given: 実行可能なAPIクライアントがある
            When:  mood_scoreが負の値で'/entries'にPOSTする
            Then:  レスポンスのステータスコードは422である
            And:   レスポンスボディにバリデーションエラーが含まれる
    """

    def test_add_entry_invalid_mood_score(self, client, dummy_entry):
        entry_dict = dummy_entry.model_dump()
        entry_dict.pop("id", None)
        entry_dict["record_date"] = dummy_entry.record_date.isoformat()
        entry_dict["mood_score"] = -1
        response = client.post("/entries", json=entry_dict)
        assert response.status_code == 422
        resp_json = response.json()
        assert "error" in resp_json.get(
            "detail", "") or "mood_score" in str(resp_json)

    """
    Feature: エントリー追加API
        Scenario: mood_scoreが6以上の場合はバリデーションエラーとなる
            Given: 実行可能なAPIクライアントがある
            When:  mood_scoreが6で'/entries'にPOSTする
            Then:  レスポンスのステータスコードは422である
            And:   レスポンスボディにバリデーションエラーが含まれる
    """

    def test_add_entry_mood_score_too_high(self, client, dummy_entry):
        entry_dict = dummy_entry.model_dump()
        entry_dict.pop("id", None)
        entry_dict["record_date"] = dummy_entry.record_date.isoformat()
        entry_dict["mood_score"] = 6
        response = client.post("/entries", json=entry_dict)
        assert response.status_code == 422
        resp_json = response.json()
        assert "error" in resp_json.get(
            "detail", "") or "mood_score" in str(resp_json)

    """
    Feature: エントリー追加API
        Scenario: sleep_hoursが負の数の場合はバリデーションエラーとなる
            Given: 実行可能なAPIクライアントがある
            When:  sleep_hoursが-1で'/entries'にPOSTする
            Then:  レスポンスのステータスコードは422である
            And:   レスポンスボディにバリデーションエラーが含まれる
    """

    def test_add_entry_sleep_hours_negative(self, client, dummy_entry):
        entry_dict = dummy_entry.model_dump()
        entry_dict.pop("id", None)
        entry_dict["record_date"] = dummy_entry.record_date.isoformat()
        entry_dict["sleep_hours"] = -1
        response = client.post("/entries", json=entry_dict)
        assert response.status_code == 422
        resp_json = response.json()
        assert "error" in resp_json.get(
            "detail", "") or "sleep_hours" in str(resp_json)

    """
    Feature: エントリー追加API
        Scenario: sleep_hoursが文字列の場合はバリデーションエラーとなる
            Given: 実行可能なAPIクライアントがある
            When:  sleep_hoursが文字列で'/entries'にPOSTする
            Then:  レスポンスのステータスコードは422である
            And:   レスポンスボディにバリデーションエラーが含まれる
    """

    def test_add_entry_invalid_sleep_hours_type(self, client, dummy_entry):
        entry_dict = dummy_entry.model_dump()
        entry_dict.pop("id", None)
        entry_dict["record_date"] = dummy_entry.record_date.isoformat()
        entry_dict["sleep_hours"] = "eight"
        response = client.post("/entries", json=entry_dict)
        assert response.status_code == 422
        resp_json = response.json()
        assert "error" in resp_json.get(
            "detail", "") or "sleep_hours" in str(resp_json)
    
    """
    Feature: エントリー追加API
    Scenario: データベースエラーが発生した場合は500エラーを返す
            Given: 実行可能なAPIクライアントがある
            When:  sleep_hoursが文字列で'/entries'にPOSTする
            Then:  レスポンスのステータスコードは500である
            And:   レスポンスボディにエラーメッセージが含まれる
    """

    def test_add_entry_database_error(self, client, dummy_entry):
        entry_dict = dummy_entry.model_dump()
        entry_dict.pop("id", None)
        entry_dict["record_date"] = dummy_entry.record_date.isoformat()
        client = self._create_client("error")
        response = client.post("/entries", json=entry_dict)
        assert response.status_code == 500
        resp_json = response.json()
        assert "detail" in resp_json
        assert "failed to insert entry" in resp_json["detail"]

    # エントリー取得APIのテスト
    """
    Feature: エントリー取得API
        Scenario: エントリーの一覧取得に成功する
            Given: 実行可能なAPIクライアントがある
            When:  '/entries'にGETリクエストを実行する
            Then:  レスポンスのステータスコードは200である
            And:   レスポンスボディのキー'status'のバリューに'success'が含まれる
            And:   レスポンスボディのキー'entries'のバリューが配列である
    """

    def test_get_entries_success(self, client):
        response = client.get("/entries")
        assert response.status_code == 200
        resp_json = response.json()
        assert resp_json["status"] == "success"
        assert "entries" in resp_json
        assert isinstance(resp_json["entries"], list)
        if len(resp_json["entries"]) > 0:
            entry = resp_json["entries"][0]
            assert "id" in entry
            assert "record_date" in entry
            assert "mood_score" in entry
            assert "sleep_hours" in entry
            assert "memo" in entry

    """
    Feature: エントリー取得API
        Scenario: エントリーが0件の場合は空配列を返す
            Given: 実行可能なAPIクライアントがある
            When:  '/entries'にGETリクエストを実行する（DB内に0件）
            Then:  レスポンスのステータスコードは200である
            And:   レスポンスボディのキー'status'のバリューに'success'が含まれる
            And:   レスポンスボディのキー'entries'のバリューが空配列である
    """

    def test_get_entries_empty(self, monkeypatch):
        client = self._create_client("empty")
        response = client.get("/entries")
        assert response.status_code == 200
        resp_json = response.json()
        assert resp_json["status"] == "success"
        assert resp_json["entries"] == []

    """
    Feature: エントリー取得API
        Scenario: データベースエラーが発生した場合は500エラーを返す
            Given: 実行可能なAPIクライアントがある
            When:  '/entries'にGETリクエストを実行する（DB接続エラー）
            Then:  レスポンスのステータスコードは500である
    """

    def test_get_entries_database_error(self, monkeypatch):
        client = self._create_client("error")
        response = client.get("/entries")
        assert response.status_code == 500
        resp_json = response.json()
        assert "detail" in resp_json
        assert "failed to retrieve entries" in resp_json["detail"]

    """
    Feature: エントリー削除API
        Scenario: 正常なIDでエントリーを削除する場合は削除後の全データを返す
            Given: 実行可能なAPIクライアントがある
            When:  有効なIDで'/entries'にDELETEリクエストを実行する
            Then:  レスポンスのステータスコードは200である
            And:   レスポンスボディのキー'status'のバリューに'success'が含まれる
            And:   レスポンスボディのキー'entries'のバリューが削除後のデータである
    """

    def test_delete_entry_success(self, client):
        response = client.delete(f"/entries?id={self.DUMMY_ID}")
        assert response.status_code == 200
        resp_json = response.json()
        assert resp_json["status"] == "success"
        assert "entries" in resp_json
        # 削除後なので空の配列（削除されたもの以外が残る）
        assert isinstance(resp_json["entries"], list)

    """
    Feature: エントリー削除API
        Scenario: 存在しないIDでエントリーを削除しようとした場合は404エラーとなる
            Given: 実行可能なAPIクライアントがある
            When:  存在しないIDで'/entries'にDELETEリクエストを実行する
            Then:  レスポンスのステータスコードは404である
            And:   レスポンスボディにエラーメッセージが含まれる
    """

    def test_delete_entry_not_found(self, monkeypatch):
        client = self._create_client("not_found")
        response = client.delete(f"/entries?id={self.DUMMY_ID}")
        assert response.status_code == 404
        resp_json = response.json()
        assert "detail" in resp_json
        assert "Entry not found" in resp_json["detail"]

    """
    Feature: エントリー削除API
        Scenario: 無効なIDフォーマットでエントリーを削除しようとした場合は422エラーとなる
            Given: 実行可能なAPIクライアントがある
            When:  無効なIDフォーマットで'/entries'にDELETEリクエストを実行する
            Then:  レスポンスのステータスコードは422である
            And:   レスポンスボディにバリデーションエラーが含まれる
    """

    def test_delete_entry_invalid_id_format(self, client):
        response = client.delete("/entries?id=invalid_id")
        assert response.status_code == 422
        resp_json = response.json()
        assert "detail" in resp_json
        assert "Invalid entry ID format" in resp_json["detail"]

    """
    Feature: エントリー削除API
        Scenario: IDパラメーターが指定されていない場合は422エラーとなる
            Given: 実行可能なAPIクライアントがある
            When:  IDパラメーターなしで'/entries'にDELETEリクエストを実行する
            Then:  レスポンスのステータスコードは422である
            And:   レスポンスボディにバリデーションエラーが含まれる
    """

    def test_delete_entry_missing_id(self, client):
        response = client.delete("/entries")
        assert response.status_code == 422
        resp_json = response.json()
        assert "detail" in resp_json

    """
    Feature: エントリー削除API
        Scenario: データベースエラーが発生した場合は500エラーを返す
            Given: 実行可能なAPIクライアントがある
            When:  '/entries'にDELETEリクエストを実行する（DB接続エラー）
            Then:  レスポンスのステータスコードは500である
    """

    def test_delete_entry_database_error(self, monkeypatch):
        client = self._create_client("error")
        response = client.delete(f"/entries?id={self.DUMMY_ID}")
        assert response.status_code == 500
        resp_json = response.json()
        assert "detail" in resp_json
        assert "failed to delete entry" in resp_json["detail"]


class TestAppStartup:
    def test_app_ci_env(self, monkeypatch):
        # ENV=ciの場合はMongoDB接続しない
        monkeypatch.setenv("ENV", "ci")
        # モジュール再読み込みでapp生成
        sys.modules.pop("app.main", None)  # キャッシュクリア
        mod = importlib.import_module("app.main")
        assert hasattr(mod, "app")
        # app.summaryにCIという文字列が含まれる
        assert "WithCI" in getattr(mod.app, "summary", "")

    def test_app_non_ci_env(self, monkeypatch):
        # ENV=developmentの場合はMongoDB接続あり
        monkeypatch.setenv("ENV", "development")
        monkeypatch.setenv("MONGODB_URI", "mongodb://dummy")
        # モジュール再読み込みでapp生成
        sys.modules.pop("app.main", None)  # キャッシュクリア
        mod = importlib.import_module("app.main")
        assert hasattr(mod, "app")
        # app.summaryにCIという文字列が含まれない
        assert "WithCI" not in getattr(mod.app, "summary", "")
