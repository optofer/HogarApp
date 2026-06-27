import os
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "hogar.db")


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = _get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS eventos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                tipo TEXT NOT NULL,
                evento TEXT NOT NULL,
                origen TEXT,
                usuario TEXT,
                detalle TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def registrar_evento(
    tipo: str,
    evento: str,
    origen: Optional[str] = None,
    usuario: Optional[str] = None,
    detalle: Optional[str] = None,
) -> bool:
    try:
        init_db()
        conn = _get_connection()
        try:
            conn.execute(
                """
                INSERT INTO eventos (timestamp, tipo, evento, origen, usuario, detalle)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    tipo,
                    evento,
                    origen,
                    usuario,
                    detalle,
                ),
            )
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception:
        return False


def obtener_eventos(limit: int = 100, tipo: Optional[str] = None) -> List[Dict[str, Any]]:
    init_db()
    conn = _get_connection()
    try:
        if tipo:
            rows = conn.execute(
                """
                SELECT timestamp, tipo, evento, origen, usuario, detalle
                FROM eventos
                WHERE tipo = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (tipo, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT timestamp, tipo, evento, origen, usuario, detalle
                FROM eventos
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()
