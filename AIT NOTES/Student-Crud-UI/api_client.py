import requests


API_BASE_URL = "http://127.0.0.1:8000"


class APIClient:

    # -------------------------------------------------
    # CREATE STUDENT
    # -------------------------------------------------

    @staticmethod
    def add_student(name, course, fee):

        url = f"{API_BASE_URL}/students"

        payload = {
            "name": name,
            "course": course,
            "fee": fee
        }

        response = requests.post(
            url,
            json=payload
        )

        return response

    # -------------------------------------------------
    # GET ALL STUDENTS
    # -------------------------------------------------

    @staticmethod
    def get_students():

        url = f"{API_BASE_URL}/students"

        response = requests.get(url)

        return response

    # -------------------------------------------------
    # GET STUDENT BY ID
    # -------------------------------------------------

    @staticmethod
    def get_student(student_id):

        url = f"{API_BASE_URL}/students/{student_id}"

        response = requests.get(url)

        return response

    # -------------------------------------------------
    # UPDATE STUDENT
    # -------------------------------------------------

    @staticmethod
    def update_student(
        student_id,
        name,
        course,
        fee
    ):

        url = f"{API_BASE_URL}/students/{student_id}"

        payload = {
            "name": name,
            "course": course,
            "fee": fee
        }

        response = requests.put(
            url,
            json=payload
        )

        return response

    # -------------------------------------------------
    # DELETE STUDENT
    # -------------------------------------------------

    @staticmethod
    def delete_student(student_id):

        url = f"{API_BASE_URL}/students/{student_id}"

        response = requests.delete(url)

        return response