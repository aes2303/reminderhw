import mysql.connector
from _mysql_connector import MySQLInterfaceError
from mysql.connector.errors import OperationalError
from datetime import datetime
from dataclasses import dataclass

@dataclass
class Database:
    host: str
    user: str
    password: str
    database: str

    def __post_init__(self):
        self.connect(database=False)
        self.create_database()
        self.disconnect()
        self.connect()
        self.create_table("homework", "id INT AUTO_INCREMENT PRIMARY KEY, subject VARCHAR(16), name VARCHAR(16), date DATETIME, description VARCHAR(100)")

    def create_database(self):
        query = f"CREATE DATABASE IF NOT EXISTS {self.database}"
        self.execute(query)

    def create_table(self, name, columns):
        query = f"CREATE TABLE IF NOT EXISTS {name} ({columns})"
        self.execute(query)

    def connect(self, database=True):
        if database:
            self.connection = mysql.connector.connect(host=self.host, user=self.user, password=self.password, database=self.database)
        else:
            self.connection = mysql.connector.connect(host=self.host, user=self.user, password=self.password)
        self.cursor = self.connection.cursor()

    def disconnect(self):
        self.connection.close()

    def execute(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
        except OperationalError:
            print("Connection lost, reconnecting...")
            self.connect(database=False)
            self.cursor.execute(query, params)
            self.connection.commit()
        except MySQLInterfaceError:
            print("Connection timeout, reconnecting...")
            self.connect(database=False)
            self.cursor.execute(query, params)
            self.connection.commit()

    def fetch(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except OperationalError:
            print("Connection lost, reconnecting...")
            self.connect(database=False)
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except MySQLInterfaceError:
            print("Connection timeout, reconnecting...")
            self.connect(database=False)
            self.cursor.execute(query, params)
            return self.cursor.fetchall()

    def fetch_one(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        except OperationalError:
            print("Connection lost, reconnecting...")
            self.connect(database=False)
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        except MySQLInterfaceError:
            print("Connection timeout, reconnecting...")
            self.connect(database=False)
            self.cursor.execute(query, params)
            return self.cursor.fetchone()

    def fetch_all(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except OperationalError:
            print("Connection lost, reconnecting...")
            self.connect(database=False)
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except MySQLInterfaceError:
            print("Connection timeout, reconnecting...")
            self.connect(database=False)
            self.cursor.execute(query, params)
            return self.cursor.fetchall()

    def add_homework(self, subject: str, name: str, date: datetime, description: str):
        query = "INSERT INTO homework (subject, name, date, description) VALUES (%s, %s, %s, %s)"
        self.execute(query, (subject, name, date.strftime("%Y-%m-%d %H:%M:%S"), description))

    def get_homework(self, id: int):
        query = "SELECT * FROM homework WHERE id = %s"
        return self.fetch_one(query, (id,))

    def get_homeworks(self):
        query = "SELECT * FROM homework WHERE date >= %s ORDER BY date"
        return self.fetch_all(query, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))

    def get_homework(self, id):
        query = "SELECT * FROM homework WHERE id = %s"
        return self.fetch_one(query, (id,))

    def delete_homework(self, id):
        query = "DELETE FROM homework WHERE id = %s"
        self.execute(query, (id,))
