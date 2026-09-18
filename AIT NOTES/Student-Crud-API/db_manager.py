import mysql.connector
from mysql.connector import Error

from config import DB_CONFIG


class DBManager:

    def __init__(self):
        self.connection = None
        self.cursor = None

        self.connect()

    # -------------------------------------------------
    # Connect to MySQL Server
    # -------------------------------------------------

    def connect(self):

        try:

            # Connect to MySQL Server
            # Database is not specified initially
            self.connection = mysql.connector.connect(
                host=DB_CONFIG["host"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"]
            )

            self.cursor = self.connection.cursor(
                dictionary=True
            )

            print("MySQL Server Connected Successfully")

        except Error as e:

            print("Database Connection Error:", e)
            raise

    # -------------------------------------------------
    # Create Database and Table
    # -------------------------------------------------

    def create_table(self):

        try:

            # Create database if it does not exist
            query = f"""
            CREATE DATABASE IF NOT EXISTS {DB_CONFIG["database"]}
            """

            self.cursor.execute(query)

            print(
                f"Database '{DB_CONFIG['database']}' "
                "checked/created successfully"
            )

            # Close existing connection
            self.cursor.close()
            self.connection.close()

            # Reconnect to the created database
            self.connection = mysql.connector.connect(
                host=DB_CONFIG["host"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                database=DB_CONFIG["database"]
            )

            self.cursor = self.connection.cursor(
                dictionary=True
            )

            # Create Students table
            query = """
            CREATE TABLE IF NOT EXISTS students
            (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                NAME VARCHAR(100) NOT NULL,
                COURSE VARCHAR(100) NOT NULL,
                FEE DECIMAL(10,2) NOT NULL
            )
            """

            self.cursor.execute(query)

            self.connection.commit()

            print(
                "Students table checked/created successfully"
            )

        except Error as e:

            if self.connection:
                self.connection.rollback()

            print("Table Creation Error:", e)
            raise

    # -------------------------------------------------
    # Execute Query
    # -------------------------------------------------

    def execute_query(self, query, values=None):

        try:

            self.cursor.execute(query, values)

            # SELECT query
            if query.strip().upper().startswith("SELECT"):

                return self.cursor.fetchall()

            # INSERT / UPDATE / DELETE
            self.connection.commit()

            return True

        except Error as e:

            self.connection.rollback()

            raise Exception(str(e))

    # -------------------------------------------------
    # Close Database Connection
    # -------------------------------------------------

    def close(self):

        if self.cursor:
            self.cursor.close()

        if self.connection:
            self.connection.close()

        print("Database Connection Closed")