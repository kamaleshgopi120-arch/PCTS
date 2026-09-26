"""
backend/mongo.py — MongoDB Connection & Tracking History Store
================================================================
This module handles MongoDB connectivity for the Parcel and Courier Tracking
System (PCTS), storing unstructured and chronological tracking event logs.

Why MongoDB for Tracking History?
---------------------------------
1. Relational vs NoSQL:
   - MySQL stores structured business entities with foreign keys (customers,
     parcels, payments).
   - MongoDB stores high-volume, append-only timeline events where schema
     flexibility allows varied metadata across different transit checkpoints.
2. Fault Tolerance (EC-21 & EC-35):
   - If MongoDB is temporarily unavailable or offline, the system continues
     serving core operations and returns MySQL status with a helpful warning:
     "Tracking history is temporarily unavailable."
"""

import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ConnectionFailure, ServerSelectionTimeoutError

# Load environment variables
load_dotenv()

logger = logging.getLogger("pcts.mongo")

# Configuration from .env
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "pcts_db")
COLLECTION_NAME = "tracking_history"

# Global client cache
_client: Optional[MongoClient] = None
_use_mock: bool = False
_mock_client: Optional[Any] = None


def get_mongo_client() -> Optional[MongoClient]:
    """
    Get or create a cached MongoDB client.
    Uses short timeouts (2000ms) to prevent blocking if MongoDB is unreachable.
    """
    global _client, _use_mock, _mock_client

    if _use_mock and _mock_client is not None:
        return _mock_client

    if _client is None:
        try:
            _client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000,
                socketTimeoutMS=2000,
            )
        except Exception as exc:
            logger.error("Failed to initialize MongoClient: %s", exc)
            return None

    return _client


def set_mock_client(mock_client: Optional[Any] = None) -> None:
    """
    Inject an in-memory mock client (e.g. mongomock) for testing purposes.
    Pass None to reset back to normal real client mode.
    """
    global _use_mock, _mock_client
    if mock_client is not None:
        _use_mock = True
        _mock_client = mock_client
    else:
        _use_mock = False
        _mock_client = None


def get_mongo_db():
    """
    Get the PCTS database instance from MongoDB, or None if unavailable.
    """
    client = get_mongo_client()
    if client is None:
        return None
    try:
        return client[MONGO_DB_NAME]
    except Exception as exc:
        logger.error("Could not access MongoDB database '%s': %s", MONGO_DB_NAME, exc)
        return None


def is_mongo_connected() -> bool:
    """
    Quickly ping MongoDB to verify server reachability.
    Returns True if reachable, False otherwise.
    """
    client = get_mongo_client()
    if client is None:
        return False
    try:
        # The 'ping' command is cheap and checks server health
        client.admin.command("ping")
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError, PyMongoError) as exc:
        logger.warning("MongoDB ping failed: %s", exc)
        return False
    except Exception as exc:
        logger.warning("Unexpected error during MongoDB ping: %s", exc)
        return False


def log_tracking_event(
    tracking_id: str,
    status: str,
    location: str,
    updated_by: str,
    notes: Optional[str] = None,
    timestamp: Optional[datetime] = None,
) -> bool:
    """
    Save an event to the 'tracking_history' collection in MongoDB.

    Document Schema (as defined in databaseDesign.md Section 3):
    {
        "tracking_id": "PCTS-20240925-0001",
        "status": "In Transit",
        "location": "Mumbai Sorting Center",
        "updated_by": "admin",
        "timestamp": ISODate("2024-09-25T10:30:00Z"),
        "notes": "Optional remarks"
    }

    Returns True if the document was inserted successfully, False if MongoDB
    is unavailable or an error occurred.
    """
    db = get_mongo_db()
    if db is None:
        logger.warning("Cannot log tracking event for '%s': MongoDB unavailable", tracking_id)
        return False

    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    elif timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    event_doc = {
        "tracking_id": tracking_id,
        "status": status,
        "location": location,
        "updated_by": updated_by,
        "timestamp": timestamp,
        "notes": notes or "",
    }

    try:
        collection = db[COLLECTION_NAME]
        result = collection.insert_one(event_doc)
        logger.info(
            "Logged tracking event for %s (status='%s') -> _id: %s",
            tracking_id,
            status,
            result.inserted_id,
        )
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError, PyMongoError) as exc:
        logger.error(
            "Failed to save tracking event to MongoDB for %s (EC-35): %s",
            tracking_id,
            exc,
        )
        return False
    except Exception as exc:
        logger.error("Unexpected error saving tracking event for %s: %s", tracking_id, exc)
        return False


def get_tracking_history(tracking_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Retrieve all tracking history events for a given parcel from MongoDB,
    ordered chronologically by timestamp ascending.

    Returns:
    - List of event dictionaries if MongoDB is reachable.
    - None if MongoDB is unavailable or unreachable (triggers EC-21).
    """
    db = get_mongo_db()
    if db is None:
        logger.warning("MongoDB unavailable while fetching history for '%s'", tracking_id)
        return None

    try:
        collection = db[COLLECTION_NAME]
        cursor = collection.find(
            {"tracking_id": tracking_id}
        ).sort("timestamp", pymongo.ASCENDING)

        events: List[Dict[str, Any]] = []
        for doc in cursor:
            events.append(
                {
                    "event_id": str(doc.get("_id", "")),
                    "tracking_id": doc.get("tracking_id"),
                    "status": doc.get("status"),
                    "location": doc.get("location"),
                    "updated_by": doc.get("updated_by"),
                    "timestamp": doc.get("timestamp"),
                    "notes": doc.get("notes"),
                }
            )
        return events
    except (ConnectionFailure, ServerSelectionTimeoutError, PyMongoError) as exc:
        logger.error(
            "MongoDB error while retrieving tracking history for %s (EC-21): %s",
            tracking_id,
            exc,
        )
        return None
    except Exception as exc:
        logger.error("Unexpected error retrieving tracking history for %s: %s", tracking_id, exc)
        return None
