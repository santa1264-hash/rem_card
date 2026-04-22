import sqlite3
from typing import Optional
from rem_card.Rao_jornal.config.settings import MKB_DB_PATH

class MKBService:
    def __init__(self):
        self.conn = sqlite3.connect(MKB_DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def get_diagnosis_by_code(self, code: str) -> Optional[str]:
        # MKB codes are often stored with periods, but users might omit them.
        # Also, case-insensitive search.
        cleaned_code = code.upper()
        self.cursor.execute("SELECT name FROM class_mkb WHERE code = ? COLLATE NOCASE", (cleaned_code,))
        row = self.cursor.fetchone()
        if row:
            return row["name"]
        return None

    def close_connection(self):
        if self.conn:
            self.conn.close()