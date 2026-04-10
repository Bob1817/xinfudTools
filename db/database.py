import sqlite3
import os
import sys
from pathlib import Path


def _get_data_dir() -> Path:
    """获取用户数据目录（跨平台兼容，支持打包环境）"""
    if getattr(sys, 'frozen', False):
        # 打包后的应用
        if sys.platform == 'win32':
            # Windows: %LOCALAPPDATA%\HR数据处理工具集
            return Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'HR数据处理工具集'
        elif sys.platform == 'darwin':
            # macOS: ~/Library/Application Support/HR数据处理工具集
            return Path.home() / 'Library' / 'Application Support' / 'HR数据处理工具集'
        else:
            # Linux: ~/.local/share/HR数据处理工具集
            return Path.home() / '.local' / 'share' / 'HR数据处理工具集'
    else:
        # 开发环境：使用项目目录
        return Path(__file__).parent.parent / 'data'


class Database:

    def __init__(self, db_path: str = None):
        if db_path is None:
            data_dir = _get_data_dir()
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / 'history.db')
        
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
