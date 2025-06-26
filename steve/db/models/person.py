from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class Person:
    """
    Represents a person model for the Steve Discord Bot.

    Attributes:
        name: str - The person's full name
        discord_id: int - Discord user ID
        eid: Optional[str] - Employee ID (default: None)
        email: Optional[str] - Email address (default: None)
        id: Optional[str] - Appwrite document ID (default: None)
    """

    name: str
    discord_id: int
    eid: Optional[str] = None
    email: Optional[str] = None
    id: Optional[str] = None

    def to_dict(self) -> dict:
        result = asdict(self)
        result.pop("id", None)
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Person":
        return cls(**data)
