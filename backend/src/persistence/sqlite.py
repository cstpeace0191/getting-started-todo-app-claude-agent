import os
import aiosqlite
from typing import List, Optional, Dict, Any

LOCATION = os.getenv("SQLITE_DB_LOCATION", "/etc/todos/todo.db")
_db: Optional[aiosqlite.Connection] = None

COLUMNS = "id, name, completed, category, priority, registered, due_date, due_time"

# 기존 DB(이전 버전으로 만든 todo.db)에 없을 수 있는 컬럼 → 시작 시 자동 추가
_NEW_COLUMNS = {
    "category": "VARCHAR(20)",
    "priority": "VARCHAR(10)",
    "registered": "BOOLEAN DEFAULT 0",
    "due_date": "VARCHAR(10)",
    "due_time": "VARCHAR(5)",
}


def _row_to_item(row: aiosqlite.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "completed": bool(row["completed"]),
        "category": row["category"],
        "priority": row["priority"],
        "registered": bool(row["registered"]),
        "due_date": row["due_date"],
        "due_time": row["due_time"],
    }


async def init() -> None:
    global _db
    dirname = os.path.dirname(os.path.abspath(LOCATION))
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    if os.getenv("NODE_ENV") != "test" and os.getenv("ENV") != "test":
        print(f"Using sqlite database at {LOCATION}")

    _db = await aiosqlite.connect(LOCATION)
    _db.row_factory = aiosqlite.Row

    await _db.execute(
        "CREATE TABLE IF NOT EXISTS todo_items ("
        "id VARCHAR(36), name VARCHAR(255), completed BOOLEAN, "
        "category VARCHAR(20), priority VARCHAR(10), registered BOOLEAN DEFAULT 0, "
        "due_date VARCHAR(10), due_time VARCHAR(5))"
    )

    # 마이그레이션: 예전 스키마(id, name, completed)에 새 컬럼 추가
    async with _db.execute("PRAGMA table_info(todo_items)") as cursor:
        existing = {row["name"] for row in await cursor.fetchall()}
    for column, col_type in _NEW_COLUMNS.items():
        if column not in existing:
            await _db.execute(f"ALTER TABLE todo_items ADD COLUMN {column} {col_type}")

    await _db.commit()


async def teardown() -> None:
    global _db
    if _db is not None:
        await _db.close()
        _db = None


def _escape_like(text: str) -> str:
    """LIKE 와일드카드(%, _)를 문자 그대로 검색하도록 이스케이프한다."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def get_items(
    search: Optional[str] = None,
    category: Optional[str] = None,
    registered: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    global _db
    if _db is None:
        await init()
    assert _db is not None
    conditions: List[str] = []
    params: List[Any] = []
    if search and search.strip():
        # SQLite 의 LIKE 는 ASCII 대소문자를 구분하지 않는다 (한글은 대소문자 없음)
        conditions.append("name LIKE ? ESCAPE '\\'")
        params.append(f"%{_escape_like(search.strip())}%")
    if category:
        conditions.append("category = ?")
        params.append(category)
    if registered is not None:
        conditions.append("COALESCE(registered, 0) = ?")
        params.append(1 if registered else 0)
    query = f"SELECT {COLUMNS} FROM todo_items"
    if conditions:
        query += " WHERE " + " AND ".join(conditions) + " ORDER BY name"
    async with _db.execute(query, params) as cursor:
        rows = await cursor.fetchall()
        return [_row_to_item(row) for row in rows]


async def get_category_counts(registered: Optional[bool] = None) -> List[Dict[str, Any]]:
    """분류(category)별 항목 개수. 분류가 없는 항목은 제외한다."""
    global _db
    if _db is None:
        await init()
    assert _db is not None
    query = "SELECT category, COUNT(*) AS count FROM todo_items WHERE category IS NOT NULL"
    params: List[Any] = []
    if registered is not None:
        query += " AND COALESCE(registered, 0) = ?"
        params.append(1 if registered else 0)
    query += " GROUP BY category ORDER BY category"
    async with _db.execute(query, params) as cursor:
        rows = await cursor.fetchall()
        return [{"category": r["category"], "count": r["count"]} for r in rows]


async def get_schedule(day: str) -> List[Dict[str, Any]]:
    """day(YYYY-MM-DD) 일정 + 기한이 지났지만 아직 완료하지 않은 항목. 시간순."""
    global _db
    if _db is None:
        await init()
    assert _db is not None
    query = (
        f"SELECT {COLUMNS} FROM todo_items "
        "WHERE due_date IS NOT NULL AND (due_date = ? "
        "OR (due_date < ? AND COALESCE(completed, 0) = 0)) "
        "ORDER BY due_date, COALESCE(due_time, '99:99'), name"
    )
    async with _db.execute(query, (day, day)) as cursor:
        rows = await cursor.fetchall()
        return [_row_to_item(row) for row in rows]


async def get_schedule_range(start: str, end: str) -> List[Dict[str, Any]]:
    """기한(due_date)이 start~end(양끝 포함, YYYY-MM-DD) 사이인 항목. 날짜·시간순."""
    global _db
    if _db is None:
        await init()
    assert _db is not None
    query = (
        f"SELECT {COLUMNS} FROM todo_items "
        "WHERE due_date IS NOT NULL AND due_date >= ? AND due_date <= ? "
        "ORDER BY due_date, COALESCE(due_time, '99:99'), name"
    )
    async with _db.execute(query, (start, end)) as cursor:
        rows = await cursor.fetchall()
        return [_row_to_item(row) for row in rows]


async def get_item(item_id: str) -> Optional[Dict[str, Any]]:
    global _db
    if _db is None:
        await init()
    assert _db is not None
    async with _db.execute(
        f"SELECT {COLUMNS} FROM todo_items WHERE id = ?", (item_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if not row:
            return None
        return _row_to_item(row)


async def store_item(item: Dict[str, Any]) -> None:
    global _db
    if _db is None:
        await init()
    assert _db is not None
    await _db.execute(
        "INSERT INTO todo_items "
        "(id, name, completed, category, priority, registered, due_date, due_time) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            item["id"],
            item["name"],
            1 if item.get("completed") else 0,
            item.get("category"),
            item.get("priority"),
            1 if item.get("registered") else 0,
            item.get("due_date"),
            item.get("due_time"),
        ),
    )
    await _db.commit()


async def update_item(item_id: str, item: Dict[str, Any]) -> None:
    global _db
    if _db is None:
        await init()
    assert _db is not None
    await _db.execute(
        "UPDATE todo_items SET name = ?, completed = ?, category = ?, priority = ?, "
        "registered = ?, due_date = ?, due_time = ? "
        "WHERE id = ?",
        (
            item["name"],
            1 if item.get("completed") else 0,
            item.get("category"),
            item.get("priority"),
            1 if item.get("registered") else 0,
            item.get("due_date"),
            item.get("due_time"),
            item_id,
        ),
    )
    await _db.commit()


async def remove_item(item_id: str) -> None:
    global _db
    if _db is None:
        await init()
    assert _db is not None
    await _db.execute("DELETE FROM todo_items WHERE id = ?", (item_id,))
    await _db.commit()


# SQLite 의 바인딩 변수 개수 제한(기본 999)을 넘지 않도록 나눠서 삭제한다
_DELETE_CHUNK = 500


async def remove_items(item_ids: List[str]) -> int:
    """여러 항목을 한 번에 삭제하고, 실제로 삭제된 개수를 돌려준다."""
    global _db
    if _db is None:
        await init()
    assert _db is not None
    deleted = 0
    for start in range(0, len(item_ids), _DELETE_CHUNK):
        chunk = item_ids[start : start + _DELETE_CHUNK]
        placeholders = ",".join("?" * len(chunk))
        async with _db.execute(
            f"DELETE FROM todo_items WHERE id IN ({placeholders})", chunk
        ) as cursor:
            deleted += cursor.rowcount
    await _db.commit()
    return deleted
