import os
import asyncio
import asyncpg
from typing import List, Optional, Dict, Any

_pool: Optional[asyncpg.Pool] = None

COLUMNS = "id, name, completed, category, priority, registered, due_date, due_time"

# 기존 DB(이전 버전으로 만든 테이블)에 없을 수 있는 컬럼 → 시작 시 자동 추가
_NEW_COLUMNS = {
    "category": "VARCHAR(20)",
    "priority": "VARCHAR(10)",
    "registered": "BOOLEAN NOT NULL DEFAULT FALSE",
    "due_date": "VARCHAR(10)",
    "due_time": "VARCHAR(5)",
}


def _row_to_item(row: asyncpg.Record) -> Dict[str, Any]:
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


def _read_env_or_file(env_var: str, file_var: str, default: str = "") -> str:
    file_path = os.getenv(file_var)
    if file_path and os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return os.getenv(env_var, default)


def _escape_like(text: str) -> str:
    """LIKE 와일드카드(%, _)를 문자 그대로 검색하도록 이스케이프한다."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def init() -> None:
    global _pool

    host = _read_env_or_file("POSTGRES_HOST", "POSTGRES_HOST_FILE", "localhost")
    user = _read_env_or_file("POSTGRES_USER", "POSTGRES_USER_FILE", "postgres")
    password = _read_env_or_file("POSTGRES_PASSWORD", "POSTGRES_PASSWORD_FILE", "")
    database = _read_env_or_file("POSTGRES_DB", "POSTGRES_DB_FILE", "todos")
    # Kubernetes 서비스 환경변수(POSTGRES_PORT=tcp://<IP>:<PORT>) 호환 처리
    raw_port = _read_env_or_file("POSTGRES_PORT", "POSTGRES_PORT_FILE", "5432")
    if raw_port.startswith("tcp://"):
        raw_port = raw_port.rsplit(":", 1)[-1]
    if not raw_port.isdigit():
        raw_port = os.getenv("POSTGRES_SERVICE_PORT", "5432")
    port = int(raw_port) if raw_port.isdigit() else 5432

    # Retry connection until database is ready (up to 30 seconds)
    max_retries = 30
    retry_interval = 1.0
    for attempt in range(max_retries):
        try:
            _pool = await asyncpg.create_pool(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                min_size=1,
                max_size=5,
            )
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"Waiting for PostgreSQL at {host}:{port}... ({e})")
            await asyncio.sleep(retry_interval)

    assert _pool is not None
    async with _pool.acquire() as conn:
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS todo_items ("
            "id VARCHAR(36) PRIMARY KEY, "
            "name VARCHAR(255), "
            "completed BOOLEAN, "
            "category VARCHAR(20), "
            "priority VARCHAR(10), "
            "registered BOOLEAN NOT NULL DEFAULT FALSE, "
            "due_date VARCHAR(10), due_time VARCHAR(5))"
        )

        # 마이그레이션: 예전 스키마에 새 컬럼 추가
        for column, col_type in _NEW_COLUMNS.items():
            await conn.execute(
                f"ALTER TABLE todo_items ADD COLUMN IF NOT EXISTS {column} {col_type}"
            )

        # 검색 가속: pg_trgm 트라이그램 인덱스 (ILIKE '%검색어%' 에도 인덱스 사용)
        # 확장 생성 권한이 없는 환경에서는 인덱스 없이도 검색은 동작한다.
        try:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_todo_items_name_trgm "
                "ON todo_items USING gin (name gin_trgm_ops)"
            )
        except Exception as e:
            print(f"pg_trgm search index not created (search still works): {e}")

    print(f"Connected to postgresql db at host {host}")


async def teardown() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def get_items(
    search: Optional[str] = None,
    category: Optional[str] = None,
    registered: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    global _pool
    if _pool is None:
        await init()
    assert _pool is not None
    conditions: List[str] = []
    params: List[Any] = []
    if search and search.strip():
        params.append(f"%{_escape_like(search.strip())}%")
        conditions.append(f"name ILIKE ${len(params)} ESCAPE '\\'")
    if category:
        params.append(category)
        conditions.append(f"category = ${len(params)}")
    if registered is not None:
        params.append(registered)
        conditions.append(f"registered = ${len(params)}")
    query = f"SELECT {COLUMNS} FROM todo_items"
    if conditions:
        query += " WHERE " + " AND ".join(conditions) + " ORDER BY name"
    async with _pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
        return [_row_to_item(row) for row in rows]


async def get_category_counts(registered: Optional[bool] = None) -> List[Dict[str, Any]]:
    """분류(category)별 항목 개수. 분류가 없는 항목은 제외한다."""
    global _pool
    if _pool is None:
        await init()
    assert _pool is not None
    query = "SELECT category, COUNT(*) AS count FROM todo_items WHERE category IS NOT NULL"
    params: List[Any] = []
    if registered is not None:
        params.append(registered)
        query += f" AND registered = ${len(params)}"
    query += " GROUP BY category ORDER BY category"
    async with _pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
        return [{"category": r["category"], "count": r["count"]} for r in rows]


async def get_schedule(day: str) -> List[Dict[str, Any]]:
    """day(YYYY-MM-DD) 일정 + 기한이 지났지만 아직 완료하지 않은 항목. 시간순."""
    global _pool
    if _pool is None:
        await init()
    assert _pool is not None
    query = (
        f"SELECT {COLUMNS} FROM todo_items "
        "WHERE due_date IS NOT NULL AND (due_date = $1 "
        "OR (due_date < $1 AND COALESCE(completed, FALSE) = FALSE)) "
        "ORDER BY due_date, COALESCE(due_time, '99:99'), name"
    )
    async with _pool.acquire() as conn:
        rows = await conn.fetch(query, day)
        return [_row_to_item(row) for row in rows]


async def get_schedule_range(start: str, end: str) -> List[Dict[str, Any]]:
    """기한(due_date)이 start~end(양끝 포함, YYYY-MM-DD) 사이인 항목. 날짜·시간순."""
    global _pool
    if _pool is None:
        await init()
    assert _pool is not None
    query = (
        f"SELECT {COLUMNS} FROM todo_items "
        "WHERE due_date IS NOT NULL AND due_date >= $1 AND due_date <= $2 "
        "ORDER BY due_date, COALESCE(due_time, '99:99'), name"
    )
    async with _pool.acquire() as conn:
        rows = await conn.fetch(query, start, end)
        return [_row_to_item(row) for row in rows]


async def get_item(item_id: str) -> Optional[Dict[str, Any]]:
    global _pool
    if _pool is None:
        await init()
    assert _pool is not None
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            f"SELECT {COLUMNS} FROM todo_items WHERE id = $1", item_id
        )
        return _row_to_item(row) if row else None


async def store_item(item: Dict[str, Any]) -> None:
    global _pool
    if _pool is None:
        await init()
    assert _pool is not None
    async with _pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO todo_items "
            "(id, name, completed, category, priority, registered, due_date, due_time) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
            item["id"],
            item["name"],
            bool(item.get("completed")),
            item.get("category"),
            item.get("priority"),
            bool(item.get("registered")),
            item.get("due_date"),
            item.get("due_time"),
        )


async def update_item(item_id: str, item: Dict[str, Any]) -> None:
    global _pool
    if _pool is None:
        await init()
    assert _pool is not None
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE todo_items SET name = $1, completed = $2, "
            "category = $3, priority = $4, registered = $5, "
            "due_date = $6, due_time = $7 WHERE id = $8",
            item["name"],
            bool(item.get("completed")),
            item.get("category"),
            item.get("priority"),
            bool(item.get("registered")),
            item.get("due_date"),
            item.get("due_time"),
            item_id,
        )


async def remove_item(item_id: str) -> None:
    global _pool
    if _pool is None:
        await init()
    assert _pool is not None
    async with _pool.acquire() as conn:
        await conn.execute("DELETE FROM todo_items WHERE id = $1", item_id)


async def remove_items(item_ids: List[str]) -> int:
    """여러 항목을 한 번에 삭제하고, 실제로 삭제된 개수를 돌려준다."""
    global _pool
    if _pool is None:
        await init()
    assert _pool is not None
    async with _pool.acquire() as conn:
        # 한 문장으로 삭제. 결과는 "DELETE <개수>" 형태의 상태 문자열
        status = await conn.execute(
            "DELETE FROM todo_items WHERE id = ANY($1::text[])", item_ids
        )
    return int(status.split()[-1])
