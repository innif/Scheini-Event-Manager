from flask import Flask, request
import sqlite3
import json
import datetime

app = Flask(__name__)
#create database
def get_db():
    db = sqlite3.connect("db/reservations.db")
    cursor = db.cursor()
    return db, cursor

def init_db():
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

def check_date(date: str):
    if date is None:
        return "Date not provided"
    if not isinstance(date, str):
        return "Date not a string"
    try:
        datetime.date.fromisoformat(date)
    except:
        return "Date not in ISO format"
    return None
    
def reservation_to_dict(input: dict):
    reservation_id, name, quantity, comment, date = input
    return {'id': reservation_id, 'name': name, 'quantity': quantity, 'comment': comment, 'date': date}

def get_reservations(date: str):
    res = check_date(date)
    if res is not None:
        return res, False
    

    db, cursor = get_db()
    cursor.execute('''
        SELECT * FROM reservierungen
        WHERE strftime('%Y-%m-%d', date) = ?
    ''', (date,))

    reservations = cursor.fetchall()
    db.close()
    reservation_dicts = [reservation_to_dict(r) for r in reservations]
    return reservation_dicts, True

def get_reservation(id: int):
    db, cursor = get_db()
    cursor.execute('''
        SELECT * FROM reservierungen
        WHERE id = ?
    ''', (id,))
    result = cursor.fetchone()
    db.close()
    if result is not None:
        return reservation_to_dict(result), True
    return "No matching reservation found", False

def add_reservation(date: str, name: str, quantity: int, comment: str):
    res = check_date(date)
    if res is not None:
        return res, False
    db, cursor = get_db()
    cursor.execute('''
        INSERT INTO reservierungen (name, quantity, comment, date)
        VALUES (?, ?, ?, ?)
    ''', (name, quantity, comment, date))
    entry_id = cursor.lastrowid

    db.commit()
    db.close()
    return entry_id, True

def edit_reservation(id: int, date: str, name: str, quantity: int, comment: str):
    res = check_date(date)
    if res is not None:
        return res, False
    db, cursor = get_db()
    cursor.execute('''
        UPDATE reservierungen
        SET name = ?, quantity = ?, comment = ?, date = ?
        WHERE id = ?
    ''', (name, quantity, comment, date, id))
    # check if something was updated
    success = cursor.rowcount > 0
    db.commit()
    db.close()
    if not success:
        return "No matching reservation found", False
    return "Reservation updated", True

def delete_reservation(id: int):
    db, cursor = get_db()
    cursor.execute('''
        DELETE FROM reservierungen
        WHERE id = ?
    ''', (id,))
    # check if something was deleted
    success = cursor.rowcount > 0
    db.commit()
    db.close()
    if not success:
        return "No matching reservation found", False
    return "Reservation deleted", True

@app.route('/')
def root_endpoint():
    return 'This is the database.', 200

@app.route('/reservations', methods=['GET'])
def reservations():
    date = request.json.get("date")
    r, success = get_reservations(date)
    return (json.dumps(r), 200) if success else ('', 400)

@app.route('/reservation', methods=['POST', 'DELETE', 'PUT', 'GET'])
def reservation():
    try:
        if request.method == 'POST':
            id, success = add_reservation(request.json.get("date"), request.json.get("name"), request.json.get("quantity"), request.json.get("comment"))
            return str(id), (201 if success else 400)
        if request.method == 'DELETE':
            message, success = delete_reservation(request.json.get("id"))
            return message, (200 if success else 400)
        if request.method == 'PUT':
            message, success = edit_reservation(request.json.get("id"), request.json.get("date"), request.json.get("name"), request.json.get("quantity"), request.json.get("comment"))
            return message, (200 if success else 400)
        if request.method == 'GET':
            r, success = get_reservation(request.json.get("id"))
            return (json.dumps(r), 200) if success else (r, 400)
    except Exception as e:
        print(e)
        return 'Error', 500
    return 'Method not allowed', 405

if __name__ == "__main__":
    app.run()