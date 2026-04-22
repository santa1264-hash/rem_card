CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    admission_uid TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_admission_uid ON patients(admission_uid);

CREATE TABLE IF NOT EXISTS admissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    bed_number INTEGER NOT NULL,
    history_number TEXT NOT NULL,
    admission_datetime DATETIME NOT NULL,
    patient_age INTEGER,
    patient_months INTEGER,
    patient_age_unit TEXT,
    patient_gender TEXT,
    diagnosis_code TEXT,
    diagnosis_text TEXT,
    department_profile TEXT,
    source_department TEXT,
    transfer_datetime DATETIME,
    transfer_department TEXT,
    outcome TEXT,
    transfer_lpu TEXT,
    transfer_lpu_other TEXT,
    death_datetime DATETIME,
    clinical_death_datetime DATETIME,
    cardiac_arrest_cause TEXT,
    cardiac_arrest_measures_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

CREATE TABLE IF NOT EXISTS operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_id INTEGER NOT NULL,
    operation_number INTEGER NOT NULL,
    description TEXT NOT NULL,
    operation_datetime DATETIME NOT NULL,
    FOREIGN KEY (admission_id) REFERENCES admissions(id)
);

CREATE TABLE IF NOT EXISTS beds (
    bed_number INTEGER PRIMARY KEY,
    status TEXT NOT NULL,
    current_admission_id INTEGER,
    FOREIGN KEY (current_admission_id) REFERENCES admissions(id)
);

CREATE TABLE IF NOT EXISTS ivl_episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_id INTEGER NOT NULL,
    episode_number INTEGER NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    type TEXT NOT NULL,
    FOREIGN KEY (admission_id) REFERENCES admissions(id)
);

CREATE TABLE IF NOT EXISTS transfusions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    volume_ml INTEGER NOT NULL,
    datetime DATETIME NOT NULL,
    source TEXT DEFAULT 'journal',
    source_order_id INTEGER,
    source_admin_id INTEGER,
    FOREIGN KEY (admission_id) REFERENCES admissions(id)
);

-- Таблицы для реанимационных карт (rao_card)
CREATE TABLE IF NOT EXISTS vitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_id INTEGER NOT NULL,
    datetime DATETIME NOT NULL,
    sys INTEGER,
    dia INTEGER,
    pulse INTEGER,
    temp REAL,
    spo2 INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admission_id) REFERENCES admissions(id)
);

CREATE TABLE IF NOT EXISTS fluids (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_id INTEGER NOT NULL,
    datetime DATETIME NOT NULL,
    iv_input REAL DEFAULT 0,
    oral_input REAL DEFAULT 0,
    food REAL DEFAULT 0,
    urine REAL DEFAULT 0,
    ng_output REAL DEFAULT 0,
    drain_output REAL DEFAULT 0,
    stool REAL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admission_id) REFERENCES admissions(id)
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_id INTEGER NOT NULL,
    datetime DATETIME NOT NULL,
    text TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admission_id) REFERENCES admissions(id)
);

CREATE TABLE IF NOT EXISTS clinical_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    event_type TEXT NOT NULL,
    author TEXT,
    data TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admission_id) REFERENCES admissions(id)
);

CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_id INTEGER NOT NULL,
    device_type TEXT NOT NULL,
    insertion_date DATETIME,
    removal_date DATETIME,
    location TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admission_id) REFERENCES admissions(id)
);

CREATE TABLE IF NOT EXISTS respiratory_support (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_id INTEGER NOT NULL,
    datetime DATETIME NOT NULL,
    mode TEXT,
    fio2 REAL,
    peep REAL,
    tv REAL,
    rr INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admission_id) REFERENCES admissions(id)
);

CREATE TABLE IF NOT EXISTS lab_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_id INTEGER NOT NULL,
    datetime DATETIME NOT NULL,
    platelets REAL,
    bilirubin REAL,
    creatinine REAL,
    lactate REAL,
    pao2 REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admission_id) REFERENCES admissions(id)
);

CREATE TABLE IF NOT EXISTS drugs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    template TEXT
);

-- Индексы для быстрого поиска по РемКартам
CREATE INDEX IF NOT EXISTS idx_vitals_admission ON vitals(admission_id, datetime);
CREATE INDEX IF NOT EXISTS idx_fluids_admission ON fluids(admission_id, datetime);
CREATE INDEX IF NOT EXISTS idx_orders_admission ON orders(admission_id, datetime);
CREATE INDEX IF NOT EXISTS idx_clinical_events_admission ON clinical_events(admission_id, timestamp);
