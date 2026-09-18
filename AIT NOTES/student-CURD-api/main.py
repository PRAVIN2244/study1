from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import FastAPI, HTTPException, status
from mysql.connector import Error
from pydantic import BaseModel, Field

import db


class Student(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    course: str = Field(min_length=1, max_length=100)
    fee: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class StudentOut(Student):
    id: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.create_table()
    yield


app = FastAPI(
    title="Student CRUD API",
    description="REST API to perform CRUD operations using a MySQL database.",
    version="1.0.0",
    lifespan=lifespan,
)


def handle_database_error(error: Error):
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Database error: {error}",
    ) from error


@app.get("/")
def welcome():
    return {"message": "Student CRUD API is running"}


@app.post("/student", status_code=status.HTTP_201_CREATED)
def create_student(student: Student):
    try:
        return db.create_student(student)
    except Error as error:
        handle_database_error(error)


@app.get("/students")
def get_all_students():
    try:
        return db.get_students()
    except Error as error:
        handle_database_error(error)


@app.get("/students/{student_id}")
def get_student_by_id(student_id: int):
    try:
        student = db.get_student_by_id(student_id)
    except Error as error:
        handle_database_error(error)

    return student


@app.put("/students/{student_id}")
def update_student(student_id: int, student: Student):
    try:
        updated_student = db.update_student(student_id, student)
    except Error as error:
        handle_database_error(error)

    return updated_student


@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    try:
        is_deleted = db.delete_student(student_id)
    except Error as error:
        handle_database_error(error)

    return is_deleted
