# ADR-003: WebフレームワークにFastAPIを採用する（Djangoではなく）

## ステータス
Accepted

## コンテキスト
Pythonでホテル予約システムのWebAPIを構築する。主要な選択肢としてDjangoとFastAPIがある。本プロジェクトではオニオンアーキテクチャ（ADR-005）を採用し、ドメイン層をインフラから完全に分離する方針である。

## 決定
**FastAPIを採用する。**

## 理由

### ドメイン層の独立性
- Django ORMは `models.Model` の継承を強制し、ドメインモデルとDBモデルが密結合になる
- FastAPIはフレームワーク固有の構造を押し付けないため、ドメインモデルをPure Pythonで記述し、インフラ層でSQLAlchemy等にマッピングできる

### アーキテクチャとの相性
- Djangoは「MTV（Model-Template-View）」構造を持ち、オニオンアーキテクチャと衝突する
- FastAPIはレイヤー構成を自由に設計できる

### リポジトリパターンとの整合
- Django ORMのQuerySetがリポジトリの役割を奪い、二重管理になりがち
- FastAPI + SQLAlchemyの組み合わせでは、リポジトリパターンを自然に実装できる

### 非同期処理
- FastAPIはネイティブasync対応。仮予約TTLのスケジューリング等に有利

### Django Adminを使わない理由
- 管理者機能は必要だが、Django Adminはドメインロジックをバイパスして直接DB操作する危険がある
- 例: Admin画面から予約ステータスを直接変更すると、キャンセル料計算やドメインイベント発行がスキップされる
- 管理者操作もドメインロジックを必ず経由すべきであり、FastAPIの管理用エンドポイントとして実装する（ADR-007）

## 結果
- WebAPIはFastAPIで構築する
- 管理者向け機能はFastAPIの管理用エンドポイントとして実装する
- Django Admin相当の機能が必要な場合はAPIとして提供する
