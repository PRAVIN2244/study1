from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from db_manager import DBManager
from models import Student, StudentUpdate


# -------------------------------------------------
# Database Manager
# -------------------------------------------------

db = DBManager()


# -------------------------------------------------
# Application Lifespan
# -------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Runs once when application starts
    print("Application Starting...")

    db.create_table()

    print("Application Started Successfully")

    yield

    # Runs once when application shuts down
    print("Application Shutting Down...")

    db.close()


# -------------------------------------------------
# FastAPI Application
# -------------------------------------------------

app = FastAPI(
    title="Student CRUD API",
    description="REST API for Student CRUD Operations",
    version="1.0.0",
    lifespan=lifespan
)


# =================================================
# CREATE
# =================================================

@app.post("/students", status_code=201)
def add_student(student: Student):

    try:

        query = """
        INSERT INTO students
        (
            NAME,
            COURSE,
            FEE
        )
        VALUES (%s, %s, %s)
        """

        db.execute_query(
            query,
            (
                student.name,
                student.course,
                student.fee
            )
        )

        return {
            "success": True,
            "message": "Student Added Successfully",
            "student": student.dict()
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =================================================
# READ ALL
# =================================================

@app.get("/students")
def get_students():

    try:

        query = """
        SELECT *
        FROM students
        """

        students = db.execute_query(query)

        return {
        "success": True,
        "Message": "Student fetched successfully",
        "student": students
    }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =================================================
# READ BY ID
# =================================================

@app.get("/students/{student_id}")
def get_student(student_id: int):

    try:

        query = """
        SELECT *
        FROM students
        WHERE ID = %s
        """

        result = db.execute_query(
            query,
            (student_id,)
        )

        if not result:

            raise HTTPException(
                status_code=404,
                detail="Student Not Found"
            )

        return result[0]

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =================================================
# UPDATE
# =================================================

@app.put("/students/{student_id}")
def update_student(
    student_id: int,
    student: StudentUpdate
):

    try:

        query = """
        UPDATE students
        SET
            NAME = %s,
            COURSE = %s,
            FEE = %s
        WHERE ID = %s
        """

        db.execute_query(
            query,
            (
                student.name,
                student.course,
                student.fee,
                student_id
            )
        )

        return {
            "success": True,
            "message": "Student Updated Successfully",
            "student": student.dict()
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =================================================
# DELETE
# =================================================

@app.delete("/students/{student_id}")
def delete_student(student_id: int):

    try:

        query = """
        DELETE FROM students
        WHERE ID = %s
        """

        db.execute_query(
            query,
            (student_id,)
        )

        return {
            "success": True,
            "message": f"Student ID: {student_id} Deleted Successfully"
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )