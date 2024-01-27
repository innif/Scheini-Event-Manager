from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import sqlite3
import datetime

app = FastAPI()

class Reservation(BaseModel):
    name: str
    quantity: int
    comment: Optional[str] = Field(None)
    date: str

def get_db():
    db = sqlite3.connect("db/reservations.db")
    cursor = db.cursor()
    return db, cursor

@app.on_event("startup")
async def startup_event():
    db, cursor = get_db()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservierungen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            comment TEXT,
            date DATE NOT NULL
        )
    ''')
    db.commit()
    db.close()

@app.post("/reservations/", summary="Create a new reservation")
async def create_reservation(reservation: Reservation):
    try:
        datetime.date.fromisoformat(reservation.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    db, cursor = get_db()
    cursor.execute('''
        INSERT INTO reservierungen (name, quantity, comment, date)
        VALUES (?, ?, ?, ?)
    ''', (reservation.name, reservation.quantity, reservation.comment, reservation.date))
    db.commit()
    db.close()
    return {"message": "Reservation created"}

@app.get("/reservations/", summary="Get all reservations")
async def get_reservations():
    db, cursor = get_db()
    cursor.execute('''
        SELECT id, name, quantity, comment, date
        FROM reservierungen
    ''')
    reservations = cursor.fetchall()
    db.close()
    return reservations

@app.get("/reservations/{reservation_id}", summary="Get a reservation by ID")
async def get_reservation(reservation_id: int):
    db, cursor = get_db()
    cursor.execute('''
        SELECT id, name, quantity, comment, date
        FROM reservierungen
        WHERE id = ?
    ''', (reservation_id,))
    reservation = cursor.fetchone()
    db.close()
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation
    
@app.put("/reservations/{reservation_id}", summary="Update a reservation")
async def update_reservation(reservation_id: int, reservation: Reservation):
    try:
        datetime.date.fromisoformat(reservation.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    db, cursor = get_db()
    cursor.execute('''
        UPDATE reservierungen
        SET name = ?, quantity = ?, comment = ?, date = ?
        WHERE id = ?
    ''', (reservation.name, reservation.quantity, reservation.comment, reservation.date, reservation_id))
    db.commit()
    db.close()
    return {"message": "Reservation updated"}

@app.delete("/reservations/{reservation_id}", summary="Delete a reservation")
async def delete_reservation(reservation_id: int):
    db, cursor = get_db()
    cursor.execute('''
        DELETE FROM reservierungen
        WHERE id = ?
    ''', (reservation_id,))
    db.commit()
    db.close()
    return {"message": "Reservation deleted"}

@app.get("/reservations/date/{date}", summary="Get reservations by date")
async def get_reservations_by_date(date: str):
    db, cursor = get_db()
    cursor.execute('''
        SELECT id, name, quantity, comment, date
        FROM reservierungen
        WHERE date = ?
    ''', (date,))
    reservations = cursor.fetchall()
    db.close()
    return reservations

@app.get("/reservations/summary/", summary="Get a summary of reservations")
def get_summary(start_date: str, end_date: str):
    db, cursor = get_db()
    cursor.execute('''
        SELECT date, COUNT(*) as num_reservations
        FROM reservierungen
        WHERE date BETWEEN ? AND ?
        GROUP BY date
    ''', (start_date, end_date))
    summary = cursor.fetchall()
    db.close()
    return summary

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)