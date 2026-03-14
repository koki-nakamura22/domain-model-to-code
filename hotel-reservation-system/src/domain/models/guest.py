"""Guest集約: ゲスト情報の管理。"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.models.shared import new_id


@dataclass(frozen=True)
class GuestName:
    first_name: str
    last_name: str


@dataclass(frozen=True)
class ContactInfo:
    email: str
    phone_number: str


@dataclass
class Guest:
    id: str
    name: GuestName
    contact_info: ContactInfo

    @staticmethod
    def create(name: GuestName, contact_info: ContactInfo) -> Guest:
        return Guest(id=new_id(), name=name, contact_info=contact_info)
