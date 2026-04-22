import sqlite3
from typing import Optional, List
from rem_card.Rao_jornal.domain.patient import Patient
from rem_card.Rao_jornal.database.db_manager import DBManager

class PatientRepository:
    def __init__(self, db_manager: DBManager):
        self.db_manager = db_manager

    def add_patient(self, patient: Patient, cursor=None) -> int:
        if cursor is not None:
            cursor.execute(
                "INSERT INTO patients (full_name, admission_uid) VALUES (?, ?)",
                (patient.full_name, patient.admission_uid)
            )
            return cursor.lastrowid
        with self.db_manager.write_transaction(source="journal_add_patient") as tx:
            tx.execute(
                "INSERT INTO patients (full_name, admission_uid) VALUES (?, ?)",
                (patient.full_name, patient.admission_uid)
            )
            return tx.lastrowid

    def get_patient_by_id(self, patient_id: int) -> Optional[Patient]:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        row = cursor.fetchone()
        if row:
            return Patient(id=row["id"], full_name=row["full_name"], admission_uid=row["admission_uid"])
        return None

    def update_patient(self, patient: Patient, cursor=None):
        if cursor is not None:
            cursor.execute(
                "UPDATE patients SET full_name = ? WHERE id = ?",
                (patient.full_name, patient.id)
            )
            return
        with self.db_manager.write_transaction(source="journal_update_patient") as tx:
            tx.execute(
                "UPDATE patients SET full_name = ? WHERE id = ?",
                (patient.full_name, patient.id)
            )

    def delete_patient(self, patient_id: int):
        with self.db_manager.write_transaction(source="journal_delete_patient") as cursor:
            cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))

    def get_all_patients(self) -> List[Patient]:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients")
        rows = cursor.fetchall()
        return [Patient(id=row["id"], full_name=row["full_name"], admission_uid=row["admission_uid"]) for row in rows]

    def get_patient_by_admission_uid(self, admission_uid: str) -> Optional[Patient]:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE admission_uid = ?", (admission_uid,))
        row = cursor.fetchone()
        if row:
            return Patient(id=row["id"], full_name=row["full_name"], admission_uid=row["admission_uid"])
        return None


