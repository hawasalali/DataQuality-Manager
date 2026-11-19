CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    phone TEXT,
    department TEXT,
    birth_date TEXT,
    hire_date TEXT,
    status TEXT DEFAULT 'VALID'
);

CREATE TABLE IF NOT EXISTS validation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER,
    column_name TEXT,
    error_message TEXT,
    severity TEXT,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS import_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    import_date TEXT,
    records_imported INTEGER,
    records_rejected INTEGER
);
