from .database import Database


def run_migrations() -> None:
    db = Database()
    conn = db.get_conn()

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            webpage_url TEXT DEFAULT '',
            title TEXT DEFAULT '',
            extractor TEXT DEFAULT '',
            uploader TEXT DEFAULT '',
            duration INTEGER DEFAULT 0,
            thumbnail TEXT DEFAULT '',
            output_path TEXT DEFAULT '',
            folder TEXT DEFAULT '',
            selected_preset TEXT DEFAULT '',
            selected_format TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            progress REAL DEFAULT 0.0,
            speed TEXT DEFAULT '',
            eta TEXT DEFAULT '',
            error_message TEXT DEFAULT '',
            format_spec TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            started_at TEXT DEFAULT '',
            completed_at TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status);
        CREATE INDEX IF NOT EXISTS idx_downloads_created ON downloads(created_at);
    """)

    db.commit()
