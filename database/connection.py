import sqlite3

class DatabaseConnection:
    def __init__(self, db_path: str = "data/employees.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_schema()

    def _create_schema(self):
        with open("database/schema.sql", "r") as f:
            self.conn.executescript(f.read())

    def close(self):
        self.conn.close()

    def get_connection(self):
        return self.conn
