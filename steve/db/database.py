from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from utils.config import (
    APPWRITE_API_KEY,
    APPWRITE_ENDPOINT,
    APPWRITE_PROJECT_ID,
)

client = Client()
client.set_endpoint(APPWRITE_ENDPOINT)
client.set_project(APPWRITE_PROJECT_ID)
client.set_key(APPWRITE_API_KEY)
database = Databases(client)
storage = Storage(client)
