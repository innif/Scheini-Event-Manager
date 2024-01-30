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

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db():
    db = sqlite3.connect("db/database.db")
    db.row_factory = dict_factory
    cursor = db.cursor()
    return db, cursor

@app.on_event("startup")
async def startup_event():
    db, cursor = get_db()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            comment TEXT,
            date DATE NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            date DATE PRIMARY KEY,
            event_kind TEXT CHECK( event_kind IN ('open_stage', 'solo', 'other') ) NOT NULL,
            moderator TEXT
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
        INSERT INTO reservations (name, quantity, comment, date)
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
        FROM reservations
    ''')
    reservations = cursor.fetchall()
    db.close()
    return reservations

@app.get("/reservations/{reservation_id}", summary="Get a reservation by ID")
async def get_reservation(reservation_id: int):
    db, cursor = get_db()
    cursor.execute('''
        SELECT id, name, quantity, comment, date
        FROM reservations
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
        UPDATE reservations
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
        DELETE FROM reservations
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
        FROM reservations
        WHERE date = ?
    ''', (date,))
    reservations = cursor.fetchall()
    db.close()
    return reservations

@app.get("/reservations/summary/", summary="Get a summary of reservations")
def get_summary(start_date: str, end_date: str):
    print("start")
    db, cursor = get_db()
    print("db")
    cursor.execute('''
        SELECT date, COUNT(*) as num_reservations
        FROM reservations, events
        WHERE date BETWEEN ? AND ?
        GROUP BY date
    ''', (start_date, end_date))
    summary = cursor.fetchall()
    print("fetch")
    db.close()
    print("close")
    return summary

@app.post("/events/", summary="Create a new event")
async def create_event(date: str, event_kind: str, moderator: Optional[str] = None):
    try:
        datetime.date.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    if event_kind not in ['open_stage', 'solo', 'other']:
        raise HTTPException(status_code=400, detail="Invalid event kind")
    
    db, cursor = get_db()
    try:
        cursor.execute('''
            INSERT INTO events (date, event_kind, moderator)
            VALUES (?, ?, ?)
        ''', (date, event_kind, moderator))
        db.commit()
    except sqlite3.IntegrityError:
        db.close()
        raise HTTPException(status_code=409, detail="Event already exists")
    db.close()
    return {"message": "Event created"}

@app.get("/events/{date}", summary="Get an event by date")
async def get_event_by_date(date: str):
    db, cursor = get_db()
    cursor.execute('''
        SELECT e.date, e.event_kind, e.moderator, COALESCE(SUM(r.quantity), 0) as num_reservations
        FROM events e
        LEFT JOIN reservations r ON e.date = r.date
        WHERE e.date = ?
        GROUP BY e.date, e.event_kind, e.moderator
    ''', (date,))
    event = cursor.fetchone()
    db.close()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@app.put("/events/{date}", summary="Update an event")
async def update_event(date: str, event_kind: str, moderator: Optional[str] = None):
    try:
        datetime.date.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    if event_kind not in ['open_stage', 'solo', 'other']:
        raise HTTPException(status_code=400, detail="Invalid event kind")
    
    db, cursor = get_db()
    cursor.execute('''
        UPDATE events
        SET event_kind = ?, moderator = ?
        WHERE date = ?
    ''', (event_kind, moderator, date))
    db.commit()
    db.close()
    return {"message": "Event updated"}

from typing import List

@app.get("/events/", summary="Get all events")
async def get_all_events(start_date: Optional[str] = None, end_date: Optional[str] = None):
    try:
        if start_date is not None:
            datetime.date.fromisoformat(start_date)
        if end_date is not None:
            datetime.date.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    db, cursor = get_db()
    query = '''
        SELECT e.date, e.event_kind, e.moderator, COALESCE(SUM(r.quantity), 0) as num_reservations
        FROM events e
        LEFT JOIN reservations r ON e.date = r.date
        WHERE 1=1
    '''
    params = []
    if start_date is not None:
        query += ' AND e.date >= ?'
        params.append(start_date)
    if end_date is not None:
        query += ' AND e.date <= ?'
        params.append(end_date)
    
    query += ' GROUP BY e.date, e.event_kind, e.moderator'
    
    cursor.execute(query, params)
    events = cursor.fetchall()
    db.close()
    return events

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)