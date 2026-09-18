"""MySQL database operations for the Student CRUD API."""

import os

import mysql.connector


DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
DB_NAME = os.getenv("MYSQL_DATABASE", "pydb")


def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


def create_table():
    """Create the database and students table when the API starts."""
    connection = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    cursor = connection.cursor()

    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
        cursor.execute(f"USE `{DB_NAME}`")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                course VARCHAR(100) NOT NULL,
                fee DECIMAL(10, 2) NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def create_student(student):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "INSERT INTO students (name, course, fee) VALUES (%s, %s, %s)",
            (student.name.strip(), student.course.strip(), student.fee),
        )
        student_id = cursor.lastrowid
        connection.commit()
        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        created_student = cursor.fetchone()
        return {
            "success": True,
            "message": "Student created successfully",
            "data": created_student,
        }
    finally:
        cursor.close()
        connection.close()


def get_students():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM students ORDER BY id")
        students = cursor.fetchall()
        return {
            "success": True,
            "message": "Students fetched successfully",
            "data": students,
        }
    finally:
        cursor.close()
        connection.close()


def get_student_by_id(student_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        if student is None:
            return {
                "success": False,
                "message": "Student not found",
                "data": None,
            }
        return {
            "success": True,
            "message": "Student found",
            "data": student,
        }
    finally:
        cursor.close()
        connection.close()


def update_student(student_id: int, student):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "UPDATE students SET name = %s, course = %s, fee = %s WHERE id = %s",
            (student.name.strip(), student.course.strip(), student.fee, student_id),
        )
        connection.commit()

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Student not found",
                "data": None,
            }

        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        return {
            "success": True,
            "message": "Student updated successfully",
            "data": cursor.fetchone(),
        }
    finally:
        cursor.close()
        connection.close()


def delete_student(student_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
        connection.commit()
        if cursor.rowcount == 0:
            return {"success": False, "message": "Student not found"}
        return {"success": True, "message": "Student deleted successfully"}
    finally:
        cursor.close()
        connection.close()
