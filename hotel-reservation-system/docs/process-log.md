# プロセスログ：ドメインモデル図→コード生成デモの進め方

> ブログ記事用の記録。どういうプロンプトで何を作り、どう進めたかをざっくり残す。
> 日付: 2026-03-14

---

## ステップ1: 題材とフォーマットの検討

### プロンプトの趣旨
「何かしらのドメインモデル図を書きたい。どういう案があるか検討したい」

### やったこと
- ドメインの候補を5つ提示（ECサイト、タスク管理、予約システム、図書館、SNS）
- 各候補の複雑さ・面白さを比較
- 図のフォーマットとしてMermaid vs draw.ioを比較検討

### 決まったこと
- **題材**: ホテル予約システム（十分な複雑さがあり、深掘りの余地がある）
- **フォーマット**: Mermaid（テキストベースでGit管理・コード生成と相性◎）
- draw.ioを原本にすると変換が脆い問題を議論し、Mermaidをsingle source of truthとした

### 生成物
- `docs/decisions/001-use-mermaid-for-domain-model.md`
- `docs/decisions/002-hotel-reservation-as-domain.md`

---

## ステップ2: 要件整理（スコープ確定）

### プロンプトの趣旨
「要件整理に進もう」→「リアルタイムで確認できるようファイルに書き出しながら進めたい」

### やったこと
- 要件定義のドラフトファイルを作成し、対話しながらステータスを更新していく方式を採用
- スコープを4カテゴリに分けて、1カテゴリずつ確認
  - コア機能（C-1〜C-3）→ 全部含める
  - 料金まわり（P-1〜P-3）→ 全部含める
  - 運用まわり（O-1〜O-3）→ チェーン対応、人数変動あり、決済はモック
  - 拡張領域（E-1〜E-3）→ 設計上は意識するが初期スコープ外
- 人数構成による料金変動の具体例を提示して判断を仰いだ（部屋タイプ×大人/子供）

### 生成物
- `docs/requirements.md`（スコープのテーブルをステータス付きで管理）

---

## ステップ3: ビジネスルールの詳細化

### プロンプトの趣旨
「何もわからないから、オススメ順で進めて」

### やったこと
- 予約ルール → 料金ルール → チェックイン/アウトルールの順で叩き台を提示
- 予約ルールでは「仮予約の概念を入れるべきか？」を議論
  - 「予約＝即確定」だと決済中に在庫が横取りされるリスクを指摘
  - 仮予約（TTL 15分）パターンを採用
- 料金ルールでは計算式・季節/曜日・人数構成・連泊割引・キャンセルポリシーの叩き台を提示
- チェックイン/アウトルールではノーショー検出も含めて一気に確定

### 生成物
- `docs/requirements.md`（セクション2: ビジネスルールを追記）

---

## ステップ4: ドメインイベント・用語集

### プロンプトの趣旨
「叩き台を一気に書いちゃって」

### やったこと
- ビジネスルールから機械的にドメインイベント10件を洗い出し
- 用語集をビジネスルールに登場した概念から整理

### 生成物
- `docs/requirements.md`（セクション3: ドメインイベント候補、セクション4: 用語集を追記）

---

## ステップ5: ドメインモデル図（Mermaid）

### プロンプトの趣旨
「進んで」（要件整理が終わったのでドメインモデル図の作成へ）

### やったこと
- 要件定義をもとに7つの集約を設計
  - Hotel, RoomType, Room, RatePlan, Guest, Reservation, Payment
- Mermaidクラス図で集約・エンティティ・値オブジェクトを表現
- 集約間はIDで参照（疎結合）
- SharedKernel（Money等）も定義
- ドメインイベントのフロー図と集約間の参照関係図も付属

### 生成物
- `docs/domain-model.md`

---

## ステップ6: ドメインイベント詳細フロー図

### プロンプトの趣旨
「各ドメインイベントの詳細フロー図って一般的には作らないものなの？」→「すべてのドメインイベントの図を1イベント1ファイルで作って」

### やったこと
- 全10イベントそれぞれに対して以下を含むファイルを作成
  - イベントペイロード（フィールド・型・説明）
  - 詳細フロー（Mermaidシーケンス図）
  - 後続処理
- 「他イベントへの参照を相対パスリンクで開けるようにしてほしい」というリクエストで、関連イベントセクションを追加
  - `←`（トリガー元）と `→`（後続イベント）の方向を示す凡例

### 生成物
- `docs/domain-events/DE-01_reservation-held.md` 〜 `DE-10_payment-failed.md`（全10ファイル）

---

## ステップ7: 管理者機能の追加

### プロンプトの趣旨
「予約情報を管理者が見たり変更できたりするのって必須じゃないのかな？」

### やったこと
- 管理者機能の必要性を確認
- Django Adminではなく、ドメインロジックを経由するAPI経由の管理機能として設計する方針を決定
- 要件定義に管理者機能カテゴリ（A-1〜A-4）を追加

### 生成物
- `docs/requirements.md`（管理者機能セクション追加）

---

## ステップ8: 技術選定

### プロンプトの趣旨
「言語はPython。uvとruffとpyright。DjangoかFastAPIか相談したい。DBはローカル完結なら何でも。オニオンアーキテクチャ。全レイヤー実装」

### やったこと
- Django vs FastAPI の比較 → FastAPI（オニオンアーキテクチャ・リポジトリパターンとの相性）
- RDB vs NoSQL の比較 → RDB/SQLite（ACIDトランザクション必須、リレーショナルなデータ）
- ORM: SQLAlchemy（ドメインモデルとDBモデルを分離可能）
- オニオンアーキテクチャのレイヤー構成を定義

### 生成物
- `docs/decisions/003-fastapi-over-django.md`
- `docs/decisions/004-rdb-sqlite-sqlalchemy.md`
- `docs/decisions/005-onion-architecture.md`
- `docs/decisions/006-code-quality-tooling.md`
- `docs/decisions/007-admin-via-api.md`
- `docs/decisions/008-held-reservation-pattern.md`
- `docs/decisions/009-payment-mock.md`

---

## 現時点のファイル構成

```
hotel-reservation-system/
├── README.md
└── docs/
    ├── process-log.md              ← 本ファイル
    ├── requirements.md             ← 要件定義
    ├── domain-model.md             ← ドメインモデル図（Mermaid）
    ├── decisions/
    │   ├── 001-use-mermaid-for-domain-model.md
    │   ├── 002-hotel-reservation-as-domain.md
    │   ├── 003-fastapi-over-django.md
    │   ├── 004-rdb-sqlite-sqlalchemy.md
    │   ├── 005-onion-architecture.md
    │   ├── 006-code-quality-tooling.md
    │   ├── 007-admin-via-api.md
    │   ├── 008-held-reservation-pattern.md
    │   └── 009-payment-mock.md
    └── domain-events/
        ├── DE-01_reservation-held.md
        ├── DE-02_reservation-expired.md
        ├── DE-03_reservation-confirmed.md
        ├── DE-04_reservation-modified.md
        ├── DE-05_reservation-cancelled.md
        ├── DE-06_guest-checked-in.md
        ├── DE-07_guest-checked-out.md
        ├── DE-08_no-show-detected.md
        ├── DE-09_payment-completed.md
        └── DE-10_payment-failed.md
```

## 次のステップ
- コードへの落とし込み（Python + FastAPI + SQLAlchemy + SQLite + オニオンアーキテクチャ）
