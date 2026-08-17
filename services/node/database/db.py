"""SQLite database for the booking service."""

import aiosqlite
import os
from pathlib import Path

from shared.utils.logger import get_logger

logger = get_logger("database")

DB_PATH = os.getenv("DB_PATH", "/tmp/trustscale_bookings.db")

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    """Get or create database connection."""
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DB_PATH)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await init_tables(_db)
        await seed_data(_db)
        logger.info("Database initialized", path=DB_PATH)
    return _db


async def close_db() -> None:
    """Close database connection."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None
        logger.info("Database closed")


async def init_tables(db: aiosqlite.Connection) -> None:
    """Create tables if they don't exist."""
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS trains (
            train_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            departure TEXT NOT NULL,
            total_seats INTEGER NOT NULL,
            available_seats INTEGER NOT NULL,
            price REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS bookings (
            booking_id TEXT PRIMARY KEY,
            train_id TEXT NOT NULL,
            passenger_name TEXT NOT NULL,
            seat_class TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'confirmed',
            booked_at TEXT NOT NULL,
            node_id TEXT NOT NULL,
            response_time_ms REAL DEFAULT 0,
            FOREIGN KEY (train_id) REFERENCES trains(train_id)
        );
    """)
    await db.commit()


async def seed_data(db: aiosqlite.Connection) -> None:
    """Seed initial train data if table is empty."""
    cursor = await db.execute("SELECT COUNT(*) FROM trains")
    row = await cursor.fetchone()

    if row[0] > 0:
        return

    trains = [
        ("RAJ001", "Rajdhani Express", "Mumbai", "Delhi", "06:00", 450, 450, 2500.0),
        ("SHA002", "Shatabdi Express", "Mumbai", "Delhi", "07:30", 300, 300, 1800.0),
        ("DUR003", "Duronto Express", "Mumbai", "Pune", "08:00", 200, 200, 800.0),
        ("GAR004", "Garib Rath", "Delhi", "Kolkata", "22:00", 500, 500, 600.0),
        ("TEJ005", "Tejas Express", "Mumbai", "Goa", "06:30", 350, 350, 1200.0),
        ("VAN006", "Vande Bharat", "Delhi", "Varanasi", "06:00", 400, 400, 1500.0),
        ("HUM007", "Humsafar Express", "Chennai", "Bangalore", "21:00", 250, 250, 900.0),
        ("MAH008", "Mahalaxmi Express", "Mumbai", "Kolhapur", "05:45", 300, 300, 450.0),
        ("DEC009", "Deccan Queen", "Mumbai", "Pune", "07:15", 200, 200, 350.0),
        ("GOA010", "Goa Express", "Mumbai", "Goa", "23:00", 400, 400, 700.0),
    ]

    await db.executemany(
        """INSERT INTO trains 
           (train_id, name, source, destination, departure, total_seats, available_seats, price)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        trains,
    )
    await db.commit()
    logger.info("Seeded train data", count=len(trains))