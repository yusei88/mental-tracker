import pytest
import os
from fastapi.testclient import TestClient


class TestOpenAPIMetadata:
    """OpenAPIメタデータの設定をテストするクラス"""

    @pytest.fixture
    def client(self):
        # CI環境で動作するように設定
        os.environ["ENV"] = "ci"
        from app.main import app
        return TestClient(app)

    def test_openapi_schema_has_tags_metadata(self, client):
        """OpenAPIスキーマにタグメタデータが含まれることをテスト"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        
        # tagsセクションが存在することを確認
        assert "tags" in openapi_spec
        assert len(openapi_spec["tags"]) == 1
        
        # entriesタグの内容を確認
        entries_tag = openapi_spec["tags"][0]
        assert entries_tag["name"] == "entries"
        assert "メンタルヘルス記録エントリーの管理操作" in entries_tag["description"]
        assert "気分スコア" in entries_tag["description"]
        assert "睡眠時間" in entries_tag["description"]

    def test_entries_endpoints_have_correct_tags(self, client):
        """全ての/entriesエンドポイントに正しいタグが設定されていることをテスト"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        entries_paths = openapi_spec["paths"]["/entries"]
        
        # 各HTTPメソッドにタグが設定されていることを確認
        for method in ["get", "post", "put", "delete"]:
            assert method in entries_paths
            assert "tags" in entries_paths[method]
            assert entries_paths[method]["tags"] == ["entries"]

    def test_entries_endpoints_have_custom_operation_ids(self, client):
        """全ての/entriesエンドポイントにカスタムoperation_idが設定されていることをテスト"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        entries_paths = openapi_spec["paths"]["/entries"]
        
        # 期待されるoperation_idのマッピング
        expected_operation_ids = {
            "get": "get_entries",
            "post": "add_entry", 
            "put": "update_entry",
            "delete": "delete_entry"
        }
        
        for method, expected_id in expected_operation_ids.items():
            assert method in entries_paths
            assert "operationId" in entries_paths[method]
            assert entries_paths[method]["operationId"] == expected_id

    def test_root_endpoint_has_no_tags(self, client):
        """ルートエンドポイント（/）にはタグが設定されていないことをテスト"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        root_path = openapi_spec["paths"]["/"]["get"]
        
        # rootエンドポイントにはタグが設定されていないことを確認
        assert "tags" not in root_path
        # デフォルトのoperationIdが使用されていることを確認
        assert root_path["operationId"] == "root__get"