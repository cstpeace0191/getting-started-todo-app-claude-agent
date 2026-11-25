import os
from . import sqlite, postgres

if os.getenv("POSTGRES_HOST") or os.getenv("POSTGRES_HOST_FILE"):
    _backend = postgres
else:
    _backend = sqlite

init = _backend.init
teardown = _backend.teardown
get_items = _backend.get_items
get_category_counts = _backend.get_category_counts
get_schedule = _backend.get_schedule
get_schedule_range = _backend.get_schedule_range
get_item = _backend.get_item
store_item = _backend.store_item
update_item = _backend.update_item
remove_item = _backend.remove_item
remove_items = _backend.remove_items

__all__ = [
    "init",
    "teardown",
    "get_items",
    "get_category_counts",
    "get_schedule",
    "get_schedule_range",
    "get_item",
    "store_item",
    "update_item",
    "remove_item",
    "remove_items",
]
