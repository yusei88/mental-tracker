# MindTrack — MVP

## 概要

**MindTrack** は、日々の気分スコアや睡眠時間、メモを記録し、シンプルな機械学習モデルで翌日の気分スコアを予測する Web アプリケーションです。  
本リポジトリは **MVP 版** のフロントエンドとバックエンドの実装例を含みます。

---

## 技術スタック

### フロントエンド

- Vue 3
- Vite
- Pinia（状態管理）
- Chart.js + vue-chartjs（グラフ描画）
- Axios（API 通信）

### バックエンド

- Python 3.11
- FastAPI
- scikit-learn（予測モデル）
- PostgreSQL（Cloud SQL 想定）

### インフラ

- Google Cloud Run（API デプロイ）
- Google Cloud SQL（データベース）
- Google Cloud Storage（静的サイトホスティング）

---

## 機能（MVP）

1. **記録投稿**: 日付、気分スコア（1〜5）、睡眠時間（h）、メモを保存
2. **記録一覧表示**: 過去の記録を取得・表示
3. **グラフ表示**: 気分スコアと睡眠時間を時系列で可視化
4. **翌日予測**: 過去データを基に翌日の気分スコアを予測

---

## ディレクトリ構成（例）

```

mindtrack/
├── backend/      # FastAPIアプリ
│ ├── main.py
│ ├── models.py
│ ├── schemas.py
│ └── ml/
│   └── model.py
├── frontend/     # Vue 3アプリ
│ ├── src/
│ │ ├── App.vue
│ │ ├── main.js
│ │ ├── components/
│ │ └── stores/
│ └── index.html
└── README.md

```

---

## セットアップ

### 1. バックエンド

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windowsは venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 2. フロントエンド

```bash
cd frontend
npm install
npm run dev
```

---

## API エンドポイント

| メソッド | パス   | 機能       |
| -------- | ------------ | -------------------- |
| POST   | /api/entries | 記録追加     |
| GET  | /api/entries | 記録一覧取得   |
| GET  | /api/predict | 翌日の気分スコア予測 |

---

## デプロイ（GCP 例）

### バックエンド（Cloud Run）

```bash
gcloud builds submit --tag gcr.io/<PROJECT_ID>/mindtrack-backend
gcloud run deploy mindtrack-backend --image gcr.io/<PROJECT_ID>/mindtrack-backend --platform managed
```

### フロントエンド（Cloud Storage）

```bash
npm run build
gsutil mb gs://<BUCKET_NAME>
gsutil cp -r dist/* gs://<BUCKET_NAME>
gsutil web set -m index.html gs://<BUCKET_NAME>
```

---

## GCP 費用（目安）

- Cloud Run: 無料枠内で月約 200 万リクエストまで無料
- Cloud SQL: 最小構成で約$7〜/月
- Cloud Storage: 数百 MB ならほぼ無料

---

## 注意点

- 無料枠を超えると課金されるため、利用状況を必ず確認すること
- MVP のため、認証・エラーハンドリングは最小限
- 本番利用時は HTTPS や OAuth2 認証を導入すること

---

## 参考リンク

- [Vue 3 公式](https://vuejs.org/)
- [Pinia 公式](https://pinia.vuejs.org/)
- [FastAPI 公式](https://fastapi.tiangolo.com/)
- [scikit-learn 公式](https://scikit-learn.org/)
- [Google Cloud Run](https://cloud.google.com/run)
- [Google Cloud SQL](https://cloud.google.com/sql)
- [Google Cloud Storage](https://cloud.google.com/storage)
