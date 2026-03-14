# DE-05: 予約キャンセル (ReservationCancelled)

## 概要
確定済みの予約がゲストによりキャンセルされた時点で発行される。キャンセルポリシーに基づきキャンセル料を算出する。

## イベントペイロード
| フィールド | 型 | 説明 |
|-----------|---|------|
| reservationId | ReservationId | 予約ID |
| reservationNumber | ReservationNumber | 予約番号 |
| hotelId | HotelId | 対象ホテル |
| guestId | GuestId | ゲストID |
| cancellationFee | Money | キャンセル料 |
| refundAmount | Money | 返金額（支払済み金額 - キャンセル料） |

## 詳細フロー

```mermaid
sequenceDiagram
    actor Guest as ゲスト
    participant RS as Reservation
    participant H as Hotel
    participant RT as RoomType
    participant PM as Payment
    participant NS as 通知サービス

    Guest->>RS: キャンセル申請(reservationId)

    RS->>RS: ステータス確認(CONFIRMED?)

    alt CONFIRMEDでない
        RS-->>Guest: エラー: キャンセル不可
    end

    RS->>H: キャンセル料計算(totalAmount, checkInDate, now)
    H-->>RS: cancellationFee

    RS->>RS: 返金額算出(totalAmount - cancellationFee)
    RS->>RS: status = CANCELLED

    Note over RS: イベント発行: ReservationCancelled

    RS->>RT: 在庫解放(roomTypeId, stayPeriod)
    RT-->>RS: 完了

    alt 返金あり
        RS->>PM: 返金依頼(refundAmount)
    end

    alt キャンセル料あり
        Note over PM: キャンセル料分は返金せず保持
    end

    RS->>NS: キャンセル通知送信依頼(guestId, reservationNumber, cancellationFee)
    NS-->>Guest: キャンセル完了通知メール
```

## 後続処理
| 処理 | 担当 | 説明 |
|------|------|------|
| キャンセル料計算 | Hotel (CancellationPolicy) | チェックイン日との日数差に基づき料金算出 |
| 在庫解放 | RoomType | 確保していた在庫を戻す |
| 返金処理 | Payment | 支払済み金額 - キャンセル料を返金 |
| キャンセル通知送信 | 通知サービス | ゲストへキャンセル完了とキャンセル料の通知 |

## 関連イベント
- ← [DE-03: 予約確定](./DE-03_reservation-confirmed.md) — 確定済みの予約がキャンセル対象
