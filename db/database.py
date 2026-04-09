import sqlite3
from pathlib import Path


class Database:

    def __init__(self, db_path: str = "data/history.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS merge_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period TEXT NOT NULL,
                source_file TEXT,
                output_file TEXT,
                total_records INTEGER,
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                note TEXT
            )
        """)
        self.conn.commit()

    def save_record(self, record: dict) -> int:
        cursor = self.conn.execute("""
            INSERT INTO merge_records
            (period, source_file, output_file, total_records, note)
            VALUES (?, ?, ?, ?, ?)
        """, (
            record["period"],
            record["source_file"],
            record["output_file"],
            record["total_records"],
            record.get("note", ""),
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_records(self, limit: int = 100) -> list[dict]:
        cursor = self.conn.execute("""
            SELECT * FROM merge_records
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def delete_record(self, record_id: int):
        self.conn.execute("DELETE FROM merge_records WHERE id = ?", (record_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()
