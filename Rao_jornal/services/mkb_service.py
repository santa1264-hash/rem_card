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
        cleaned_code = code.strip().upper()
        candidates = [cleaned_code]
        if not cleaned_code.endswith(("+", "*")):
            candidates.extend([f"{cleaned_code}+", f"{cleaned_code}*"])

        placeholders = ", ".join("?" for _ in candidates)
        self.cursor.execute(
            f"""
            SELECT name
            FROM class_mkb
            WHERE code COLLATE NOCASE IN ({placeholders})
            ORDER BY CASE UPPER(code)
                WHEN ? THEN 0
                WHEN ? THEN 1
                WHEN ? THEN 2
                ELSE 3
            END
            LIMIT 1
            """,
            (*candidates, cleaned_code, f"{cleaned_code}+", f"{cleaned_code}*"),
        )
        row = self.cursor.fetchone()
        if row:
            return row["name"]
        return None

    def close_connection(self):
        if self.conn:
            self.conn.close()
