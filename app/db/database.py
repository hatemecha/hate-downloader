import sqlite3
import threading

from app.utils.paths import ensure_dirs, get_db_path


class Database:
    _instance: "Database | None" = None
    _conn: sqlite3.Connection | None = None
    _lock = threading.RLock()

    def __new__(cls) -> "Database":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> sqlite3.Connection:
        with self._lock:
            if self._conn is None:
                ensure_dirs()
                db_path = get_db_path()
                self._conn = sqlite3.connect(
                    str(db_path),
                    check_same_thread=False,
                )
                self._conn.row_factory = sqlite3.Row
                self._conn.execute("PRAGMA journal_mode=WAL")
                self._conn.execute("PRAGMA foreign_keys=ON")
            return self._conn

    def get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            return self.connect()
        return self._conn

    def close(self) -> None:
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            return self.get_conn().execute(sql, params)

    def executemany(self, sql: str, params: list[tuple]) -> sqlite3.Cursor:
        with self._lock:
            return self.get_conn().executemany(sql, params)

    def commit(self) -> None:
        with self._lock:
            if self._conn:
                self._conn.commit()
