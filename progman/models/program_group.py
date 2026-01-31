"""ProgramGroup dataclass for organizing program items."""

from dataclasses import dataclass, field
from typing import List

from .program_item import ProgramItem


@dataclass
class ProgramGroup:
    """Container for a list of ProgramItems."""

    title: str
    items: List[ProgramItem] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "ProgramGroup":
        items_data = data.get("items", [])
        items = [ProgramItem.from_dict(i) for i in items_data]
        return cls(title=data.get("title", ""), items=items)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "items": [i.to_dict() for i in self.items],
        }
