import asyncio
from typing import Optional

from appwrite.id import ID
from appwrite.input_file import InputFile
from utils import (
    APPWRITE_BUCKET_ID_MEETINGS,
    APPWRITE_COLLECTION_ID_MEETINGS,
    APPWRITE_DB_ID,
    get_logger,
)

from .database import database, storage
from .models import Meeting

logger = get_logger(__name__)


async def create_meeting(meeting: Meeting) -> Optional[Meeting]:
    """Create a meeting in the Appwrite database.

    Args:
        meeting (Meeting): Meeting instance to create in the database

    Returns:
        Optional[str]: Document ID if successful, None if failed
    """
    try:
        response = await asyncio.to_thread(
            database.create_document,
            database_id=APPWRITE_DB_ID,
            collection_id=APPWRITE_COLLECTION_ID_MEETINGS,
            document_id=ID.unique(),
            data=meeting.to_dict(),
        )
        logger.info(f"Meeting created successfully: {response}")
        # Use from_dict to properly handle the response
        response_data = {
            k: v for k, v in dict(response).items() if not k.startswith("$")
        }
        response_data["id"] = response["$id"]
        return Meeting.from_dict(response_data)
    except Exception as e:
        logger.error(f"Error creating meeting: {e}")
        return None


async def delete_meeting(id: str) -> bool:
    """Delete a meeting from the Appwrite database.

    Args:
        id (str): Document ID of the meeting to delete

    Returns:
        bool: True if successful, False if failed
    """
    try:
        await asyncio.to_thread(
            database.delete_document,
            database_id=APPWRITE_DB_ID,
            collection_id=APPWRITE_COLLECTION_ID_MEETINGS,
            document_id=id,
        )
        logger.info(f"Meeting deleted successfully: {id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting meeting: {e}")
        return False


async def create_recording(file_name: str, file_data) -> Optional[str]:
    """Create a meeting recording file in the meetings storage bucket.

    Args:
        file_name (str): Name of the file to upload
        file_data: File content to upload (bytes or file-like object)

    Returns:
        Optional[str]: File ID if successful, None if failed
    """
    try:
        # Handle different file input types
        if hasattr(file_data, "read"):
            # File-like object (from SafeWaveSink)
            file_data.seek(0)  # Ensure we're at the beginning
            file_bytes = file_data.read()
            input_file = InputFile.from_bytes(file_bytes, filename=file_name)
        else:
            # Assume it's already bytes
            input_file = InputFile.from_bytes(file_data, filename=file_name)

        response = await asyncio.to_thread(
            storage.create_file,
            bucket_id=APPWRITE_BUCKET_ID_MEETINGS,
            file_id=ID.unique(),
            file=input_file,
        )
        logger.info(f"File created successfully: {response}")
        return response["$id"]
    except Exception as e:
        logger.error(f"Error creating file: {e}")
        return None


async def update_meeting(id: str, meeting: Meeting) -> bool:
    """Update a meeting in the Appwrite database.

    Args:
        id (str): Document ID of the meeting to update
        meeting (Meeting): Meeting instance with updated data

    Returns:
        bool: True if successful, False if failed
    """
    try:
        response = await asyncio.to_thread(
            database.update_document,
            database_id=APPWRITE_DB_ID,
            collection_id=APPWRITE_COLLECTION_ID_MEETINGS,
            document_id=id,
            data=meeting.to_dict(),
        )
        logger.info(f"Meeting updated successfully: {response}")
        return True
    except Exception as e:
        logger.error(f"Error updating meeting: {e}")
        return False


async def get_meeting(id: str) -> Optional[Meeting]:
    """Get a meeting from the Appwrite database.

    Args:
        id (str): Document ID of the meeting to retrieve

    Returns:
        Optional[Meeting]: Meeting instance if found, None if not found or error
    """
    try:
        response = await asyncio.to_thread(
            database.get_document,
            database_id=APPWRITE_DB_ID,
            collection_id=APPWRITE_COLLECTION_ID_MEETINGS,
            document_id=id,
        )
        logger.info(f"Meeting retrieved successfully: {response}")
        # Map Appwrite response to Meeting model
        response_data = {
            k: v for k, v in dict(response).items() if not k.startswith("$")
        }
        response_data["id"] = response["$id"]
        return Meeting.from_dict(response_data)
    except Exception as e:
        logger.error(f"Error retrieving meeting: {e}")
        return None
