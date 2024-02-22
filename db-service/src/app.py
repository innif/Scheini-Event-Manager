from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from pydantic import BaseModel, Field
from typing import Optional
import sqlite3
import datetime
import json
import hashlib

app = FastAPI()
security = HTTPBasic()
secrets_object = json.load(open("secrets.json"))

class Reservation(BaseModel):
    name: str
    quantity: int
    comment: Optional[str] = Field(None)
    date: str

class Event(BaseModel):
    event_kind: str
    moderator: Optional[str] = Field(None)
    comment: Optional[str] = Field(None)

class Artist(BaseModel):
    name: str
    description: Optional[str] = Field(None)
    description_short: Optional[str] = Field(None)
    image: Optional[str] = Field(None)
    website: Optional[str] = Field(None)

class Employee(BaseModel):
    name: str
    email: Optional[str] = Field(None)
    username: Optional[str] = Field(None)
    password: Optional[str] = Field(None)
    roles: list[str]

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
            event_id INTEGER REFERENCES events(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE,
            event_kind TEXT CHECK( event_kind IN ('open_stage', 'solo', 'other') ) NOT NULL,
            moderator_id INTEGER REFERENCES artists(id) ON DELETE SET NULL,
            description TEXT,
            description_short TEXT,
            image TEXT,
            comment TEXT,
            technician TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS artists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            description_short TEXT,
            image TEXT,
            website TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            event_id INTEGER REFERENCES events(id),
            artist_id INTEGER REFERENCES artists(id),
            comment TEXT,
            PRIMARY KEY (event_id, artist_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            username TEXT,
            password TEXT,
            roles LIST TEXT CHECK( roles IN ('technik', 'tresen', 'etc') ) NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS works_at (
            employee_id INTEGER REFERENCES employees(id),
            event_id INTEGER REFERENCES events(id),
            role TEXT CHECK( role IN ('technik', 'tresen', 'etc') ) NOT NULL,
            PRIMARY KEY (employee_id, event_id)
        )
    ''')
    db.commit()
    db.close()

def get_event_id(date):
    db, cursor = get_db()
    cursor.execute('''
        SELECT id
        FROM events
        WHERE date = ?
    ''', (date,))
    event_id = cursor.fetchone()
    db.close()
    return event_id

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, secrets_object.get("username"))
    correct_password = secrets.compare_digest(credentials.password, secrets_object.get("password"))
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.post("/reservations/", summary="Create a new reservation")
async def create_reservation(reservation: Reservation, username: str = Depends(get_current_username)):
    try:
        datetime.date.fromisoformat(reservation.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    db, cursor = get_db()
    cursor.execute(''' SELECT date FROM events WHERE date = ? ''', (reservation.date,))
    if cursor.fetchone() is None:
        db.close()
        raise HTTPException(status_code=404, detail="Event not found")
    cursor.execute('''
        INSERT INTO reservations (name, quantity, comment, event_id)
        VALUES (?, ?, ?, (SELECT id FROM events WHERE date = ?))
    ''', (reservation.name, reservation.quantity, reservation.comment, reservation.date))
    reservation_id = cursor.lastrowid
    db.commit()
    db.close()
    return {"message": "Reservation created", "reservation_id": reservation_id}

@app.get("/reservations/", summary="Get all reservations")
async def get_reservations(username: str = Depends(get_current_username)):
    db, cursor = get_db()
    cursor.execute('''
        SELECT r.id, r.name, r.quantity, r.comment, r.event_id, e.date
        FROM reservations r, events e
        WHERE r.event_id = e.id
    ''')
    reservations = cursor.fetchall()
    db.close()
    return reservations

@app.get("/reservations/{reservation_id}", summary="Get a reservation by ID")
async def get_reservation(reservation_id: int, username: str = Depends(get_current_username)):
    db, cursor = get_db()
    cursor.execute('''
        SELECT r.id, r.name, r.quantity, r.comment, r.event_id, e.date
        FROM reservations as r, events as e
        WHERE r.id = ? AND r.event_id = e.id
    ''', (reservation_id,))
    reservation = cursor.fetchone()
    db.close()
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation
    
@app.put("/reservations/{reservation_id}", summary="Update a reservation")
async def update_reservation(reservation_id: int, reservation: Reservation, username: str = Depends(get_current_username)):
    try:
        datetime.date.fromisoformat(reservation.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    db, cursor = get_db()
    cursor.execute('''
        UPDATE reservations
        SET name = ?, quantity = ?, comment = ?, event_id = (SELECT id FROM events WHERE date = ?)
        WHERE id = ?
    ''', (reservation.name, reservation.quantity, reservation.comment, reservation.date, reservation_id))
    db.commit()
    db.close()
    return {"message": "Reservation updated"}

@app.delete("/reservations/{reservation_id}", summary="Delete a reservation")
async def delete_reservation(reservation_id: int, username: str = Depends(get_current_username)):
    db, cursor = get_db()
    cursor.execute('''
        DELETE FROM reservations
        WHERE id = ?
    ''', (reservation_id,))
    db.commit()
    db.close()
    return {"message": "Reservation deleted"}

@app.get("/reservations/date/{date}", summary="Get reservations by date")
async def get_reservations_by_date(date: str, username: str = Depends(get_current_username)):
    db, cursor = get_db()
    cursor.execute('''
        SELECT r.id, r.name, r.quantity, r.comment, r.event_id, e.date
        FROM reservations as r, events as e
        WHERE e.date = ? AND r.event_id = e.id
    ''', (date,))
    reservations = cursor.fetchall()
    db.close()
    return reservations

@app.get("/reservations/summary/", summary="Get a summary of reservations")
async def get_summary(start_date: str, end_date: str, username: str = Depends(get_current_username)):
    db, cursor = get_db()
    cursor.execute('''
        SELECT e.date, COUNT(*) as num_reservations
        FROM reservations as r, events as e
        WHERE date BETWEEN ? AND ? AND r.event_id = e.id
        GROUP BY date
    ''', (start_date, end_date))
    summary = cursor.fetchall()
    db.close()
    return summary

@app.post("/events/", summary="Create a new event")
async def create_event(date: str, event: Event, username: str = Depends(get_current_username)):
    try:
        datetime.date.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    if event.event_kind not in ['open_stage', 'solo', 'other']:
        raise HTTPException(status_code=400, detail="Invalid event kind")
    
    db, cursor = get_db()
    try:
        cursor.execute('''SELECT date from events WHERE date = ?''', (date,))
        if cursor.fetchone() is not None:
            print("Date exists")
            raise sqlite3.IntegrityError
        artist_id = None

        # Check if artist exists
        cursor.execute('''
            SELECT id FROM artists WHERE name = ?
        ''', (event.moderator,))
        result = cursor.fetchone()
        print(result)
        if result is not None:
            artist_id = result.get("id")
        else:
            # Create a new artist
            cursor.execute('''
                INSERT INTO artists (name) VALUES (?)
            ''', (event.moderator,))
            artist_id = cursor.lastrowid

        # Insert event with artist.id as moderator
        cursor.execute('''
            INSERT INTO events (date, event_kind, moderator_id)
            VALUES (?, ?, ?)
        ''', (date, event.event_kind, artist_id))
        db.commit()
    except sqlite3.IntegrityError:
        db.close()
        raise HTTPException(status_code=409, detail="Event already exists")
    db.close()
    return {"message": "Event created"}

@app.get("/events/{date}", summary="Get an event by date")
async def get_event_by_date(date: str, username: str = Depends(get_current_username)):
    db, cursor = get_db()
    cursor.execute('''
        SELECT e.id, e.date, e.event_kind, e.comment, a.name as moderator, COALESCE((SELECT SUM(quantity) FROM reservations WHERE event_id = e.id), 0) as num_reservations, COUNT(DISTINCT b.artist_id) as num_artists, e.moderator_id
        FROM events e, artists a
        LEFT JOIN bookings b ON e.id = b.event_id
        WHERE e.moderator_id = a.id AND e.date = ?
    ''', (date,))
    event = cursor.fetchone()
    db.close()
    return event

@app.put("/events/{date}", summary="Update an event")
async def update_event(date: str, event: Event, username: str = Depends(get_current_username)):
    try:
        datetime.date.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    if event.event_kind not in ['open_stage', 'solo', 'other']:
        raise HTTPException(status_code=400, detail="Invalid event kind")
    
    db, cursor = get_db()

    # Check if artist exists
    artist_id = None
    cursor.execute('''
        SELECT id FROM artists WHERE name = ?
    ''', (event.moderator,))
    result = cursor.fetchone()
    if result is not None:
        artist_id = result.get("id")
    else:
        # Create a new artist
        cursor.execute('''
            INSERT INTO artists (name) VALUES (?)
        ''', (event.moderator,))
        artist_id = cursor.lastrowid

    cursor.execute('''
        UPDATE events
        SET event_kind = ?, moderator_id = ?, comment = ?
        WHERE date = ?
    ''', (event.event_kind, artist_id, event.comment, date))
    db.commit()
    db.close()
    return {"message": "Event updated"}

@app.delete("/events/{date}", summary="Delete an event")
async def delete_event(date: str, username: str = Depends(get_current_username)):
    db, cursor = get_db()
    cursor.execute('''
        DELETE FROM events
        WHERE date = ?
    ''', (date,))
    db.commit()
    db.close()
    return {"message": "Event deleted"}

@app.get("/events/", summary="Get all events")
async def get_all_events(start_date: Optional[str] = None, end_date: Optional[str] = None, username: str = Depends(get_current_username)):
    try:
        if start_date is not None:
            datetime.date.fromisoformat(start_date)
        if end_date is not None:
            datetime.date.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    db, cursor = get_db()
    query = '''
        SELECT e.id, e.date, e.event_kind, e.comment, a.name as moderator, COALESCE((SELECT SUM(quantity) FROM reservations WHERE event_id = e.id), 0) as num_reservations, COUNT(DISTINCT b.artist_id) as num_artists
        FROM events e, artists a
        LEFT JOIN bookings b ON e.id = b.event_id
        WHERE e.moderator_id = a.id
    '''
    params = []
    if start_date is not None:
        query += ' AND e.date >= ?'
        params.append(start_date)
    if end_date is not None:
        query += ' AND e.date <= ?'
        params.append(end_date)
    
    query += 'GROUP BY e.id'
    
    cursor.execute(query, params)
    events = cursor.fetchall()
    db.close()
    return events

@app.get("/events/{date}/next", summary="Get the next event")
async def get_next_event(date: str, username: str = Depends(get_current_username)):
    db, cursor = get_db()
    cursor.execute('''
        SELECT e.date
        FROM events e
        WHERE e.date > ?
        ORDER BY e.date ASC
        LIMIT 1
    ''', (date,))
    event = cursor.fetchone()
    db.close()
    return event

@app.get("/events/{date}/previous", summary="Get the previous event")
async def get_previous_event(date: str, username: str = Depends(get_current_username)):
    db, cursor = get_db()
    cursor.execute('''
        SELECT e.date
        FROM events e
        WHERE e.date < ?
        ORDER BY e.date DESC
        LIMIT 1
    ''', (date,))
    event = cursor.fetchone()
    db.close()
    return event

@app.get("/artists/", summary="Get all artists")
async def get_all_artists(username: str = Depends(get_current_username)):
    db, cursor = get_db()
    cursor.execute('''
        SELECT id, name, description, description_short, image, website
        FROM artists
    ''')
    artists = cursor.fetchall()
    db.close()
    return artists

@app.get("/artists/{artist_id}", summary="Get an artist by ID")
async def get_artist_by_id(artist_id: int, username: str = Depends(get_current_username)):
    db, cursor = get_db()
    cursor.execute('''
        SELECT id, name, description, description_short, image, website
        FROM artists
        WHERE id = ?
    ''', (artist_id,))
    artist = cursor.fetchone()
    db.close()
    return artist

@app.post("/artists/", summary="Create a new artist")
async def create_artist(artist: Artist, username: str = Depends(get_current_username)):
    db, cursor = get_db()
    cursor.execute('''
        INSERT INTO artists (name, description, description_short, image, website)
        VALUES (?, ?, ?, ?, ?)
    ''', (artist.name.strip(), artist.description.strip(), artist.description_short.strip(), artist.image.strip(), artist.website.strip()))
    artist_id = cursor.lastrowid
    db.commit()
    db.close()
    return {"message": "Artist created", "artist_id": artist_id}

@app.put("/artists/{artist_id}", summary="Update an artist")
async def update_artist(artist_id: int, artist: Artist, username: str = Depends(get_current_username)):
    db, cursor = get_db()
    cursor.execute('''
        UPDATE artists
        SET name = ?, description = ?, description_short = ?, image = ?, website = ?
        WHERE id = ?
    ''', (artist.name.strip(), artist.description.strip(), artist.description_short.strip(), artist.image.strip(), artist.website.strip(), artist_id))
    db.commit()
    db.close()
    return {"message": "Artist updated"}

@app.delete("/artists/{artist_id}", summary="Delete an artist")
async def delete_artist(artist_id: int, username: str = Depends(get_current_username)):
    db, cursor = get_db()
    cursor.execute('''
        DELETE FROM artists
        WHERE id = ?
    ''', (artist_id,))
    db.commit()
    db.close()
    return {"message": "Artist deleted"}

@app.get("/artists/event/{date}", summary="Get all artists for a specific date")
async def get_artists_by_date(date: str, username: str = Depends(get_current_username)):
    db, cursor = get_db()
    cursor.execute('''
        SELECT a.id, a.name, a.description, a.description_short, a.image, a.website, b.comment
        FROM artists a, bookings b, events e
        WHERE e.date = ? AND e.id = b.event_id AND a.id = b.artist_id
    ''', (date,))
    artists = cursor.fetchall()
    db.close()
    return artists

@app.post("/bookings/", summary="Create a new booking")
async def create_booking(event_id: int, artist: str, comment: Optional[str] = None, username: str = Depends(get_current_username)):
    artist = artist.strip()
    db, cursor = get_db()
    cursor.execute('''
        SELECT id FROM artists WHERE name = ?
    ''', (artist,))
    artist_id = cursor.fetchone()
    if artist_id is None:
        # create artist
        cursor.execute('''
            INSERT INTO artists (name) VALUES (?)
        ''', (artist,))
        artist_id = cursor.lastrowid
    else:
        artist_id = artist_id.get("id")
    try:
        cursor.execute('''
            INSERT INTO bookings (event_id, artist_id, comment)
            VALUES (?, ?, ?)
        ''', (event_id, artist_id, comment))
        db.commit()
    except sqlite3.IntegrityError:
        db.close()
        raise HTTPException(status_code=409, detail="Booking already exists")
    db.close()
    return {"message": "Booking created"}

@app.delete("/bookings/", summary="Delete a booking")
async def delete_booking(event_id: int, artist_id: int, username: str = Depends(get_current_username)):
    db, cursor = get_db()
    cursor.execute('''
        DELETE FROM bookings
        WHERE event_id = ? AND artist_id = ?
    ''', (event_id, artist_id))
    db.commit()
    db.close()
    return {"message": "Booking deleted"}

@app.put("/bookings/", summary="Update a booking")
async def update_booking(event_id: int, artist_id: int, comment: str, username: str = Depends(get_current_username)):
    db, cursor = get_db()
    cursor.execute('''
        UPDATE bookings
        SET comment = ?
        WHERE event_id = ? AND artist_id = ?
    ''', (comment, event_id, artist_id))
    db.commit()
    db.close()
    return {"message": "Booking updated"}

@app.put("/execute_sql/", summary="Execute a custom SQL command")
async def execute_sql(command: str, username: str = Depends(get_current_username)):
    db, cursor = get_db()
    try:
        cursor.execute(command)
        db.commit()
    except Exception as e:
        db.close()
        raise HTTPException(status_code=400, detail=str(e))
    db.close()
    return {"message": "Command executed"}

@app.get("/execute_sql/", summary="Execute a custom SQL query")
async def execute_sql_query(command: str, username: str = Depends(get_current_username)):
    db, cursor = get_db()
    try:
        cursor.execute(command)
        result = cursor.fetchall()
    except Exception as e:
        db.close()
        raise HTTPException(status_code=400, detail=str(e))
    db.close()
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)