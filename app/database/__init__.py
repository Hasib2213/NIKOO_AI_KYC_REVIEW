"""Compatibility shim: expose `db_client` and `MongoDBClient`.

Database files have been renamed:
- AIchatbotDatabase.py: Contains MongoDBClient (sync)
- KYCdatabase.py: Contains MongoDB (async)
"""
import importlib.util
import os
import sys

# Path to the sibling module file `app/database/AIchatbotDatabase.py`
this_dir = os.path.dirname(__file__)
module_path = os.path.join(this_dir, "AIchatbotDatabase.py")

if os.path.exists(module_path):
    spec = importlib.util.spec_from_file_location("app._chatbot_database_module", module_path)
    _mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = _mod
    spec.loader.exec_module(_mod)

    # Re-export expected symbols
    try:
        db_client = getattr(_mod, "db_client")
    except AttributeError:
        db_client = None

    try:
        MongoDBClient = getattr(_mod, "MongoDBClient")
    except AttributeError:
        MongoDBClient = None

    __all__ = [name for name in ("db_client", "MongoDBClient") if globals().get(name) is not None]
else:
    # Fallback: file not found
    db_client = None
    MongoDBClient = None
    __all__ = []
