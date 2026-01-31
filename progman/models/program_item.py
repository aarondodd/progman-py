"""ProgramItem dataclass for individual launchable programs."""

from dataclasses import asdict, dataclass


@dataclass
class ProgramItem:
    """Represents a single launchable program entry."""

    title: str
    command: str
    working_dir: str = ""
    icon_path: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "ProgramItem":
        return cls(
            title=data.get("title", ""),
            command=data.get("command", ""),
            working_dir=data.get("working_dir", ""),
            icon_path=data.get("icon_path", ""),
        )

    def to_dict(self) -> dict:
        return asdict(self)
