# ============================================================
# database.py — SQLite persistence layer
# ============================================================
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "urine_analyzer.db")


# ── Connection helper ────────────────────────────────────

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ── Schema initialisation ────────────────────────────────

def init_db() -> None:
    """Create tables if they do not exist."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS patients (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL COLLATE NOCASE,
                created_at TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS scans (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id       INTEGER NOT NULL
                                 REFERENCES patients(id) ON DELETE CASCADE,
                scan_date        TEXT    NOT NULL,
                glucose          TEXT    NOT NULL DEFAULT '---',
                ph               TEXT    NOT NULL DEFAULT '---',
                specific_gravity TEXT    NOT NULL DEFAULT '---',
                protein          TEXT    NOT NULL DEFAULT '---',
                created_at       TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            );
        """)


# ── Patient operations ───────────────────────────────────

def add_patient(name: str) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO patients (name) VALUES (?)", (name.strip(),)
        )
        return cur.lastrowid


def get_all_patients(search: str = "") -> list:
    with _connect() as conn:
        if search:
            rows = conn.execute(
                "SELECT * FROM patients WHERE name LIKE ? ORDER BY name",
                (f"%{search.strip()}%",),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM patients ORDER BY name"
            ).fetchall()
    return [dict(r) for r in rows]


def get_patient(patient_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        ).fetchone()
    return dict(row) if row else None


def patient_exists(name: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM patients WHERE name = ? COLLATE NOCASE", (name.strip(),)
        ).fetchone()
    return row is not None


# ── Scan operations ──────────────────────────────────────

def add_scan(patient_id: int, results: dict) -> int:
    """
    results keys: glucose, ph, specific_gravity, protein
    Returns the new scan id.
    """
    scan_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO scans
                (patient_id, scan_date, glucose, ph, specific_gravity, protein)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                scan_date,
                results.get("glucose",          "---"),
                results.get("ph",               "---"),
                results.get("specific_gravity", "---"),
                results.get("protein",          "---"),
            ),
        )
        return cur.lastrowid


def get_patient_scans(patient_id: int) -> list:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM scans WHERE patient_id = ? ORDER BY created_at DESC",
            (patient_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_scan(scan_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT s.*, p.name AS patient_name "
            "FROM scans s JOIN patients p ON s.patient_id = p.id "
            "WHERE s.id = ?",
            (scan_id,),
        ).fetchone()
    return dict(row) if row else None


def delete_scan(scan_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM scans WHERE id = ?", (scan_id,))


def delete_patient(patient_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
