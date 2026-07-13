import os

import psycopg2
from fastapi import FastAPI


app = FastAPI()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        database=os.getenv("PGDATABASE", "sysmon_lab"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", ""),
        port=int(os.getenv("PGPORT", "5432")),
    )


@app.get("/")
def root():
    return {"status": "log api online"}


@app.get("/logs")
def get_logs():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    source_host,
                    source_type,
                    provider_name,
                    event_id,
                    severity,
                    time_created,
                    message
                FROM log_events
                ORDER BY inserted_at DESC
                LIMIT 100
                """
            )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "host": row[1],
            "source_type": row[2],
            "provider": row[3],
            "event_id": row[4],
            "severity": row[5],
            "time_created": str(row[6]),
            "message": row[7],
        }
        for row in rows
    ]


@app.get("/logs/provider/{provider}")
def get_by_provider(provider: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    source_host,
                    provider_name,
                    event_id,
                    time_created,
                    message
                FROM log_events
                WHERE provider_name ILIKE %s
                ORDER BY inserted_at DESC
                LIMIT 100
                """,
                (f"%{provider}%",),
            )
            rows = cur.fetchall()

    return [
        {
            "host": row[0],
            "provider": row[1],
            "event_id": row[2],
            "time_created": str(row[3]),
            "message": row[4],
        }
        for row in rows
    ]


@app.get("/logs/event/{event_id}")
def get_by_event(event_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    source_host,
                    provider_name,
                    event_id,
                    time_created,
                    message
                FROM log_events
                WHERE event_id = %s
                ORDER BY inserted_at DESC
                LIMIT 100
                """,
                (event_id,),
            )
            rows = cur.fetchall()

    return [
        {
            "host": row[0],
            "provider": row[1],
            "event_id": row[2],
            "time_created": str(row[3]),
            "message": row[4],
        }
        for row in rows
    ]


@app.get("/stats/event-counts")
def event_counts():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT event_id, COUNT(*)
                FROM log_events
                GROUP BY event_id
                ORDER BY COUNT(*) DESC
                """
            )
            rows = cur.fetchall()

    return [{"event_id": row[0], "count": row[1]} for row in rows]


@app.get("/logs/search")
def search_logs(term: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    source_host,
                    source_type,
                    provider_name,
                    event_id,
                    severity,
                    time_created,
                    message
                FROM log_events
                WHERE message ILIKE %s
                   OR provider_name ILIKE %s
                   OR source_host ILIKE %s
                ORDER BY inserted_at DESC
                LIMIT 100
                """,
                (f"%{term}%", f"%{term}%", f"%{term}%"),
            )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "host": row[1],
            "source_type": row[2],
            "provider": row[3],
            "event_id": row[4],
            "severity": row[5],
            "time_created": str(row[6]),
            "message": row[7],
        }
        for row in rows
    ]


@app.get("/logs/source/{source_type}")
def get_by_source(source_type: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    source_host,
                    source_type,
                    provider_name,
                    event_id,
                    severity,
                    time_created,
                    message
                FROM log_events
                WHERE source_type ILIKE %s
                ORDER BY inserted_at DESC
                LIMIT 100
                """,
                (f"%{source_type}%",),
            )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "host": row[1],
            "source_type": row[2],
            "provider": row[3],
            "event_id": row[4],
            "severity": row[5],
            "time_created": str(row[6]),
            "message": row[7],
        }
        for row in rows
    ]


@app.get("/metrics/latest")
def latest_metrics():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    host_name,
                    cpu_percent,
                    memory_percent,
                    disk_percent,
                    boot_time,
                    collected_at
                FROM host_metrics
                ORDER BY collected_at DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()

    if row is None:
        return {"message": "No metrics found"}

    return {
        "id": row[0],
        "host": row[1],
        "cpu_percent": float(row[2]) if row[2] is not None else None,
        "memory_percent": float(row[3]) if row[3] is not None else None,
        "disk_percent": float(row[4]) if row[4] is not None else None,
        "boot_time": str(row[5]),
        "collected_at": str(row[6]),
    }


@app.get("/metrics")
def get_metrics():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    host_name,
                    cpu_percent,
                    memory_percent,
                    disk_percent,
                    boot_time,
                    collected_at
                FROM host_metrics
                ORDER BY collected_at DESC
                LIMIT 100
                """
            )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "host": row[1],
            "cpu_percent": float(row[2]) if row[2] is not None else None,
            "memory_percent": float(row[3]) if row[3] is not None else None,
            "disk_percent": float(row[4]) if row[4] is not None else None,
            "boot_time": str(row[5]),
            "collected_at": str(row[6]),
        }
        for row in rows
    ]

