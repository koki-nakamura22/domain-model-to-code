---
paths:
  - "hotel-reservation-system/src/**/*.py"
---

# オニオンアーキテクチャのルール

- レイヤー間の依存方向は `hotel-reservation-system/docs/decisions/005-onion-architecture.md` に従うこと
- 特に以下の違反をしないこと:
  - `domain/` から `application/`, `infrastructure/`, `presentation/` をimportしない
  - `application/` から `infrastructure/`, `presentation/` をimportしない
