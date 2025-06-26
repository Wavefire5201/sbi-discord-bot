from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Meeting:
    """
    Represents a meeting record with all associated data.

    - channel_id: int
    - guild_id: int
    - start: datetime
    - meeting_log: Optional[dict] = None
    - end: Optional[datetime] = None
    - participants: List[int] = field(default_factory=list)
    - recordings: List[str] = field(default_factory=list)
    - transcription: Optional[str] = None
    - id: Optional[str] = None
    """

    channel_id: int
    guild_id: int
    start: datetime
    meeting_log: Optional[dict] = None
    end: Optional[datetime] = None
    participants: List[int] = field(default_factory=list)
    recordings: List[str] = field(default_factory=list)
    transcription: Optional[str] = None
    id: Optional[str] = None

    def to_dict(self) -> dict:
        """
        Convert the Meeting instance to a dictionary suitable for database storage.

        Returns:
            dict: Dictionary representation of the meeting with datetime objects
                 converted to ISO format strings.
        """
        data = asdict(self)

        # Convert datetime objects to ISO format strings for database storage
        if self.start:
            data["start"] = self.start.isoformat()

        if self.end:
            data["end"] = self.end.isoformat()

        data.pop("id", None)

        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Meeting":
        """
        Create a Meeting instance from a dictionary (e.g., from database).

        Args:
            data (dict): Dictionary containing meeting data

        Returns:
            Meeting: Meeting instance created from the dictionary data
        """
        # Make a copy to avoid modifying the original data
        data = dict(data)

        # Convert ISO format strings back to datetime objects
        if "start" in data and isinstance(data["start"], str):
            data["start"] = datetime.fromisoformat(data["start"])

        if "end" in data and data["end"] and isinstance(data["end"], str):
            data["end"] = datetime.fromisoformat(data["end"])

        # Ensure participants and recordings are lists
        if "participants" not in data:
            data["participants"] = []
        if "recordings" not in data:
            data["recordings"] = []

        return cls(**data)

    def add_participant(self, user_id: int) -> None:
        """
        Add a participant to the meeting.

        Args:
            user_id (int): Discord user ID to add to participants
        """
        if user_id not in self.participants:
            self.participants.append(user_id)

    def remove_participant(self, user_id: int) -> None:
        """
        Remove a participant from the meeting.

        Args:
            user_id (int): Discord user ID to remove from participants
        """
        if user_id in self.participants:
            self.participants.remove(user_id)

    def add_recording(self, recording_id: str) -> None:
        """
        Add a recording to the meeting.

        Args:
            recording_id (str): ID of the recording file from meetings bucket
        """
        if recording_id not in self.recordings:
            self.recordings.append(recording_id)

    def end_meeting(self, end_time: Optional[datetime] = None) -> None:
        """
        End the meeting by setting the end datetime.

        Args:
            end_time (Optional[datetime]): End time for the meeting.
                                         If None, uses current datetime.
        """
        self.end = end_time or datetime.now()

    def is_active(self) -> bool:
        """
        Check if the meeting is currently active (has started but not ended).

        Returns:
            bool: True if meeting is active, False otherwise
        """
        now = datetime.now()
        return self.start <= now and (self.end is None or self.end > now)

    def duration(self) -> Optional[float]:
        """
        Calculate the duration of the meeting in seconds.

        Returns:
            Optional[float]: Duration in seconds if meeting has ended, None otherwise
        """
        if self.end:
            return (self.end - self.start).total_seconds()
        return None

    def get_log(self) -> Optional[dict]:
        """
        Get the meeting log.

        Returns:
            Optional[dict]: Meeting log content
        """
        return self.meeting_log

    def edit_log(self, new_log: Optional[dict]) -> None:
        """
        Edit the meeting log.

        Args:
            new_log (Optional[dict]): New meeting log content
        """
        self.meeting_log = new_log
