"""Booking API endpoints for the node service."""

import uuid
from datetime import datetime
from time import perf_counter

import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.node.config.behavior_config import get_current_behavior
from services.node.config.settings import settings
from services.node.monitoring.request_tracker import tracker
from services.node.database.db import get_db
from shared.utils.logger import get_logger

logger = get_logger("booking")

router = APIRouter(prefix="/api", tags=["booking"])


class BookingRequest(BaseModel):
    """Ticket booking request."""

    train_id: str
    passenger_name: str
    seat_class: str = "SL"


class BookingResponse(BaseModel):
    """Ticket booking response."""

    booking_id: str
    train_id: str
    train_name: str
    passenger_name: str
    seat_class: str
    status: str
    node_id: str
    response_time_ms: float
    seats_remaining: int


class TrainInfo(BaseModel):
    """Train information."""

    train_id: str
    name: str
    source: str
    destination: str
    departure: str
    total_seats: int
    available_seats: int
    price: float


@router.get("/trains")
async def list_trains() -> list[TrainInfo]:
    """List all available trains."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM trains ORDER BY departure"
    )
    rows = await cursor.fetchall()

    return [
        TrainInfo(
            train_id=row["train_id"],
            name=row["name"],
            source=row["source"],
            destination=row["destination"],
            departure=row["departure"],
            total_seats=row["total_seats"],
            available_seats=row["available_seats"],
            price=row["price"],
        )
        for row in rows
    ]


@router.get("/trains/{train_id}")
async def get_train(train_id: str) -> TrainInfo:
    """Get details of a specific train."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM trains WHERE train_id = ?",
        (train_id,),
    )
    row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Train not found")

    return TrainInfo(
        train_id=row["train_id"],
        name=row["name"],
        source=row["source"],
        destination=row["destination"],
        departure=row["departure"],
        total_seats=row["total_seats"],
        available_seats=row["available_seats"],
        price=row["price"],
    )


@router.post("/book")
async def book_ticket(request: BookingRequest) -> BookingResponse:
    """Book a train ticket."""
    await tracker.request_started()
    start = perf_counter()

    try:
        # If node is lying, simulate the overload effect
        behavior = get_current_behavior()
        if behavior.name != "HonestBehavior":
            import random

            # Scale delay by behavior intensity
            # Higher intensity = more overloaded = worse performance
            max_delay = 2.0 + (behavior.intensity * 4.0)
            delay = random.uniform(0.5, max_delay)
            await asyncio.sleep(delay)

            # Failure probability scales with intensity
            # intensity 0.8 = 40% failure rate
            failure_chance = behavior.intensity * 0.6
            if random.random() < failure_chance:
                duration_ms = (perf_counter() - start) * 1000
                await tracker.request_completed(duration_ms)
                raise HTTPException(
                    status_code=503,
                    detail=f"Server overloaded — node {settings.node_id} cannot process request",
                )

        db = await get_db()

        cursor = await db.execute(
            "SELECT * FROM trains WHERE train_id = ?",
            (request.train_id,),
        )
        train = await cursor.fetchone()

        if not train:
            raise HTTPException(status_code=404, detail="Train not found")

        if train["available_seats"] <= 0:
            raise HTTPException(status_code=409, detail="No seats available")

        booking_id = f"BK-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        booked_at = datetime.now().isoformat()

        await db.execute(
            """INSERT INTO bookings 
               (booking_id, train_id, passenger_name, seat_class, status, booked_at, node_id)
               VALUES (?, ?, ?, ?, 'confirmed', ?, ?)""",
            (booking_id, request.train_id, request.passenger_name,
             request.seat_class, booked_at, settings.node_id),
        )

        await db.execute(
            "UPDATE trains SET available_seats = available_seats - 1 WHERE train_id = ?",
            (request.train_id,),
        )

        await db.commit()

        duration_ms = (perf_counter() - start) * 1000

        logger.info(
            "Ticket booked",
            booking_id=booking_id,
            train=train["name"],
            passenger=request.passenger_name,
            node_id=settings.node_id,
            duration_ms=round(duration_ms, 2),
        )

        return BookingResponse(
            booking_id=booking_id,
            train_id=request.train_id,
            train_name=train["name"],
            passenger_name=request.passenger_name,
            seat_class=request.seat_class,
            status="confirmed",
            node_id=settings.node_id,
            response_time_ms=round(duration_ms, 2),
            seats_remaining=train["available_seats"] - 1,
        )

    finally:
        duration_ms = (perf_counter() - start) * 1000
        await tracker.request_completed(duration_ms)


@router.get("/bookings/{booking_id}")
async def get_booking(booking_id: str):
    """Get booking details."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT b.*, t.name as train_name, t.source, t.destination
           FROM bookings b 
           JOIN trains t ON b.train_id = t.train_id
           WHERE b.booking_id = ?""",
        (booking_id,),
    )
    row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    return {
        "booking_id": row["booking_id"],
        "train_id": row["train_id"],
        "train_name": row["train_name"],
        "route": f"{row['source']} → {row['destination']}",
        "passenger_name": row["passenger_name"],
        "seat_class": row["seat_class"],
        "status": row["status"],
        "booked_at": row["booked_at"],
        "node_id": row["node_id"],
    }


@router.get("/stats")
async def get_stats():
    """Get booking statistics for this node."""
    db = await get_db()

    booking_count = await db.execute("SELECT COUNT(*) FROM bookings WHERE node_id = ?", (settings.node_id,))
    count = (await booking_count.fetchone())[0]

    total_trains = await db.execute("SELECT COUNT(*) FROM trains")
    trains = (await total_trains.fetchone())[0]

    total_seats = await db.execute("SELECT SUM(available_seats) FROM trains")
    seats = (await total_seats.fetchone())[0]

    return {
        "node_id": settings.node_id,
        "bookings_processed": count,
        "total_trains": trains,
        "total_seats_available": seats or 0,
    }