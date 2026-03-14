# ADR-006: コード品質ツールにuv・ruff・pyrightを採用する

## ステータス
Accepted

## コンテキスト
Pythonプロジェクトのパッケージ管理、リンティング、型チェックのツールを選定する。

## 決定

| 用途 | ツール | 役割 |
|------|--------|------|
| パッケージ管理・仮想環境 | **uv** | 高速なPythonパッケージマネージャ。pip + venv + pip-tools の統合代替 |
| リンター・フォーマッター | **ruff** | 高速なPythonリンター兼フォーマッター。flake8 + black + isort の統合代替 |
| 型チェック | **pyright** | 静的型チェッカー。ドメインモデルの型安全性を担保 |

## 理由

### uv
- pip + venvより大幅に高速
- `pyproject.toml` ベースで設定が統一される
- lockファイルによる再現性のある依存管理

### ruff
- flake8 + black + isortを1ツールで代替。設定の分散を防ぐ
- Rust実装で高速

### pyright
- ドメインモデルの型定義（値オブジェクト、列挙型等）の整合性をコンパイル時に検証
- Protocolによるリポジトリインターフェースの型チェックが厳密
- mypyより高速で、VSCodeとの統合が優れている

## 結果
- `pyproject.toml` にruff・pyrightの設定を集約する
- CI/ローカルで `ruff check` + `ruff format` + `pyright` を実行する
