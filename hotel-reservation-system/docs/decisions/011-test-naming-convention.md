# ADR-011: テストケース名にドメイン寄りの命名規則を採用する

## ステータス
Accepted

## コンテキスト
テストケース名の命名方法として、技術的な表現（`test_returns_1_0`、`test_sets_completed`）とドメイン寄りの表現（`test_full_charge`、`test_reservation_confirmed`）がある。

## 決定
**`test_<状況>__<期待結果>` の形式で、ドメインの言葉を使って命名する。** 状況と期待結果はダブルアンダースコア（`__`）で区切る。

## 命名規則

```python
# パターン
test_<状況>__<期待結果>

# 良い例（ドメイン寄り）
test_cancel_on_checkin_day__full_charge
test_guest_never_shows_up__marked_as_no_show
test_3_adults_in_twin_for_2__extra_bed_fee_applied
test_all_rooms_booked__reservation_rejected

# 避ける例（技術寄り）
test_cancel_same_day__returns_1_0
test_mark_no_show__sets_status_to_no_show
test_occupancy_adjustment__returns_5000
test_create_reservation__raises_value_error
```

## 理由

### テスト一覧が仕様書として読める
- `pytest -v` の出力がそのままビジネスルールのドキュメントになる
- テストが落ちたとき、名前だけで「何のビジネスルールが壊れたか」が分かる

### ダブルアンダースコアで区切る理由
- シングルアンダースコアは単語の区切りに使うため、状況と期待結果の境界が曖昧になる
- `__` で明確に分離することで可読性が上がる

### 日本語ではなく英語を使う理由
- CI出力での文字化け回避
- 英語でもドメイン用語（charge, discount, booking, no-show等）を使えば十分読める

## 結果
- すべてのテストケースはこの命名規則に従う
- テスト名は技術的な戻り値やステータス名ではなく、ビジネス的に何が起きるかを表現する
