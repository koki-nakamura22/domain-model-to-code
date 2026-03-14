# ADR-010: テストフレームワークにpytestを採用する

## ステータス
Accepted

## コンテキスト
ユニットテストのフレームワークとして、標準ライブラリのunittest、pytest、その他（ward等）を検討した。

## 決定
**pytestを採用する。**

## 理由

### asyncとの相性
- ユースケースがすべて`async def`であり、pytest-asyncioを使うことで`async def test_*`がそのまま動作する
- unittestでは`asyncio.run`を自前で書く必要がある

### 記述の簡潔さ
- 関数ベースで`assert`文だけで書ける。unittestのクラスベース + `self.assertEqual`は冗長
- `@pytest.mark.parametrize`でパラメタライズテストが簡潔に書ける

### フィクスチャの柔軟性
- `@pytest.fixture`でリポジトリのインメモリ実装やドメインオブジェクトのセットアップをDI的に注入できる
- unittestの`setUp/tearDown`より再利用性が高い

### 導入コスト
- すでにdev依存に`pytest`と`pytest-asyncio`が含まれており、追加作業不要

## 結果
- テストはpytestで記述する
- 非同期テストにはpytest-asyncioを使用する
- Protocolベースのリポジトリはインメモリ実装に差し替えてテストする
