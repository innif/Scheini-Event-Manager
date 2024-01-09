import sqlite3
import datetime

class database:
    def __init__(self) -> None:
        '''connect to database and create tables if not exists'''
        self.conn = sqlite3.connect('example.db')
        self.c = self.conn.cursor()
        #create table for events if not exists
        # each event has a unique id, name, date, counter-employee-text and technician-text and enum for kind of event
        self.c.execute('''CREATE TABLE IF NOT EXISTS events
                (id INTEGER PRIMARY KEY AUTOINCREMENT, name text, date text, counter text, technician text, kind text)''')
        # create table for reservations if not exists
        # each reservation has a name, a quantity, an event, and a text for comments
        self.c.execute('''CREATE TABLE IF NOT EXISTS reservations
                (id INTEGER PRIMARY KEY AUTOINCREMENT, name text, quantity integer, event integer, comment text,
                       FOREIGN KEY(event) REFERENCES events(id))''')
        # create table for artists
        # each entry has a name, a description, an image and a website
        self.c.execute('''CREATE TABLE IF NOT EXISTS artists
                (id INTEGER PRIMARY KEY AUTOINCREMENT, name text, description text, image text, website text)''')
        # create table for bookings
        # each entry links an artist 
        self.c.execute('''CREATE TABLE IF NOT EXISTS bookings
                (id INTEGER PRIMARY KEY AUTOINCREMENT, artist integer, event integer,
                       FOREIGN KEY(artist) REFERENCES artists(id), FOREIGN KEY(event) REFERENCES events(id))''')

    def get_event(self, date: str):
        '''get event from database'''
        self.c.execute("SELECT * FROM events WHERE date=?", (date,))
        return self.c.fetchone()
    
    def get_reservation(self, event_id):
        '''get reservation from database'''
        self.c.execute("SELECT * FROM reservations WHERE event=?", (event_id,))
        return self.c.fetchall()
    
    def get_artist(self, event_id):
        '''get artist from database'''
        self.c.execute("SELECT * FROM artists WHERE event=?", (event_id,))
        return self.c.fetchall()
    
    def add_reservation(self, name, quantity, event_id, comment):
        '''add reservation to database'''
        self.c.execute("INSERT INTO reservations (name, quantity, event, comment) VALUES (?, ?, ?, ?)", (name, quantity, event_id, comment))
        self.conn.commit()

    def create_event(self, date: str):
        '''create event'''
        try:
            datetime.date.fromisoformat(date)
        except:
            return
        self.c.execute("INSERT INTO events (date) VALUES (?)", (date,))
        self.conn.commit()
        return self.get_event(date) # TODO return event

    def edit_event(self, event_id, name = None, date = None, counter = None, technician = None, kind = None):
        '''edit event'''
        if name is not None:
            self.c.execute("UPDATE events SET name=? WHERE id=?", (name, event_id))
        if date is not None:
            self.c.execute("UPDATE events SET date=? WHERE id=?", (date, event_id))
        if counter is not None:
            self.c.execute("UPDATE events SET counter=? WHERE id=?", (counter, event_id))
        if technician is not None:
            self.c.execute("UPDATE events SET technician=? WHERE id=?", (technician, event_id))
        if kind is not None:
            self.c.execute("UPDATE events SET kind=? WHERE id=?", (kind, event_id))
        self.conn.commit()

    def edit_reservation(self, reservation_id, name = None, quantity = None, event_id = None, comment = None):
        '''edit reservation'''
        if name is not None:
            self.c.execute("UPDATE reservations SET name=? WHERE id=?", (name, reservation_id))
        if quantity is not None:
            self.c.execute("UPDATE reservations SET quantity=? WHERE id=?", (quantity, reservation_id))
        if event_id is not None:
            self.c.execute("UPDATE reservations SET event=? WHERE id=?", (event_id, reservation_id))
        if comment is not None:
            self.c.execute("UPDATE reservations SET comment=? WHERE id=?", (comment, reservation_id))
        self.conn.commit()

    def print_events(self):
        '''print all events'''
        self.c.execute("SELECT * FROM events")
        print(self.c.fetchall())

    def get_future_events(self):
        '''get all future events as a list ordered by date'''
        self.c.execute("SELECT * FROM events WHERE date >= date('now') ORDER BY date")
        return self.c.fetchall()

    def get_reservation_count(self, event_id):
        '''get the number of reservations for an event'''
        self.c.execute("SELECT COUNT(*) FROM reservations WHERE event=?", (event_id,))
        return self.c.fetchone()[0]    
    
    def get_artist_count(self, event_id):
        '''get the number of artists for an event'''
        self.c.execute("SELECT COUNT(*) FROM bookings WHERE event=?", (event_id,))
        return self.c.fetchone()[0]