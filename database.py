import mysql.connector

class Database:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.create_database()
        self.connection = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_database(self):
        cnx = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password
        )
        cursor = cnx.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
        cnx.commit()
        cursor.close()
        cnx.close()

    def create_tables(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS homework (subject VARCHAR(255), hw VARCHAR(255), due_date VARCHAR(255), PRIMARY KEY (subject, hw, due_date))")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS subjects (subject VARCHAR(255) PRIMARY KEY)")
        self.connection.commit()

    def add_hw(self, subject, hw, due_date):
        self.cursor.execute("SELECT * FROM homework WHERE subject = %s AND hw = %s AND due_date = %s", (subject, hw, due_date))
        if self.cursor.fetchone():
            return False
        self.cursor.execute("INSERT INTO homework (subject, hw, due_date) VALUES (%s, %s, %s)", (subject, hw, due_date))
        self.connection.commit()
        return True

    def get_hw(self, subject):
        self.cursor.execute("SELECT hw, due_date FROM homework WHERE subject = %s", (subject,))
        return self.cursor.fetchall()

    def get_all_hw(self):
        self.cursor.execute("SELECT subject, hw, due_date FROM homework")
        return self.cursor.fetchall()

    def delete_hw(self, subject, hw, due_date):
        self.cursor.execute("SELECT * FROM homework WHERE subject = %s AND hw = %s AND due_date = %s", (subject, hw, due_date))
        if not self.cursor.fetchone():
            return False
        self.cursor.execute("DELETE FROM homework WHERE subject = %s AND hw = %s AND due_date = %s", (subject, hw, due_date))
        self.connection.commit()

    def add_subject(self, subject):
        self.cursor.execute("SELECT * FROM subjects WHERE subject = %s", (subject,))
        if self.cursor.fetchone():
            return False
        self.cursor.execute("INSERT INTO subjects (subject) VALUES (%s)", (subject,))
        self.connection.commit()
        return True

    def get_subjects(self):
        self.cursor.execute("SELECT subject FROM subjects")
        return self.cursor.fetchall()

    def delete_subject(self, subject):
        self.cursor.execute("SELECT * FROM subjects WHERE subject = %s", (subject,))
        if not self.cursor.fetchone():
            return False
        self.cursor.execute("DELETE FROM subjects WHERE subject = %s", (subject,))
        self.connection.commit()

    def close(self):
        self.connection.close()
