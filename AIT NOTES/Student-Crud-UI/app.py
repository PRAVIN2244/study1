import streamlit as st
import pandas as pd

from api_client import APIClient


# =================================================
# PAGE CONFIGURATION
# =================================================

st.set_page_config(
    page_title="Student Management System",
    page_icon="🎓",
    layout="wide"
)


# =================================================
# CUSTOM CSS
# =================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 36px;
        font-weight: bold;
        margin-bottom: 10px;
    }

    .sub-title {
        font-size: 18px;
        color: #666;
        margin-bottom: 30px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =================================================
# HELPER METHODS
# =================================================

def get_students_data():

    try:

        response = APIClient.get_students()

        if response.status_code == 200:

            data = response.json()

            return data.get("student", [])

        st.error(
            f"Unable to fetch students: "
            f"{response.text}"
        )

        return []

    except requests.exceptions.ConnectionError:

        st.error(
            "Unable to connect to FastAPI server."
        )

        return []

    except Exception as e:

        st.error(str(e))

        return []


# =================================================
# SIDEBAR
# =================================================

st.sidebar.title("🎓 Student Management")

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Add Student",
        "View Students",
        "Update Student",
        "Delete Student"
    ]
)

st.sidebar.markdown("---")

st.sidebar.info(
    "FastAPI + MySQL + Streamlit"
)


# =================================================
# DASHBOARD
# =================================================

if page == "Dashboard":

    st.markdown(
        '<div class="main-title">'
        '🎓 Welcome to Student Management System!'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">'
        'Manage students data using FastAPI REST APIs'
        '</div>',
        unsafe_allow_html=True
    )

    students = get_students_data()

    if students:

        df = pd.DataFrame(students)

        total_students = len(df)

        total_fees = df["FEE"].sum()

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Total Students",
                total_students
            )

        with col2:

            st.metric(
                "Total Fees",
                f"₹{total_fees:,.2f}"
            )

        st.markdown("---")

        st.subheader("Recent Students")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No students found.")


# =================================================
# ADD STUDENT
# =================================================

elif page == "Add Student":

    st.title("➕ Add Student")

    st.write(
        "Enter student details below."
    )

    with st.form("add_student_form"):

        name = st.text_input(
            "Student Name"
        )

        course = st.text_input(
            "Course"
        )

        fee = st.number_input(
            "Course Fee",
            min_value=0.01,
            step=100.00
        )

        submit = st.form_submit_button(
            "Add Student"
        )

        if submit:

            if not name.strip():

                st.error(
                    "Student name is required."
                )

            elif not course.strip():

                st.error(
                    "Course is required."
                )

            else:

                response = APIClient.add_student(
                    name,
                    course,
                    fee
                )

                if response.status_code == 201:

                    data = response.json()

                    st.success(
                        data.get(
                            "message",
                            "Student Added Successfully"
                        )
                    )

                else:

                    st.error(
                        response.text
                    )


# =================================================
# VIEW STUDENTS
# =================================================

elif page == "View Students":

    st.title("📋 Students")

    if st.button("🔄 Refresh"):

        st.rerun()

    students = get_students_data()

    if students:

        df = pd.DataFrame(students)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No students available."
        )


# =================================================
# UPDATE STUDENT
# =================================================

elif page == "Update Student":

    st.title("✏️ Update Student")

    student_id = st.number_input(
        "Student ID",
        min_value=1,
        step=1
    )

    if st.button("Get Student"):

        response = APIClient.get_student(
            student_id
        )

        if response.status_code == 200:

            student = response.json()

            st.session_state["student"] = student

        elif response.status_code == 404:

            st.error(
                "Student Not Found"
            )

        else:

            st.error(
                response.text
            )

    if "student" in st.session_state:

        student = st.session_state["student"]

        with st.form("update_student_form"):

            name = st.text_input(
                "Student Name",
                value=student["NAME"]
            )

            course = st.text_input(
                "Course",
                value=student["COURSE"]
            )

            fee = st.number_input(
                "Course Fee",
                min_value=0.01,
                value=float(student["FEE"]),
                step=100.00
            )

            update = st.form_submit_button(
                "Update Student"
            )

            if update:

                response = APIClient.update_student(
                    student_id,
                    name,
                    course,
                    fee
                )

                if response.status_code == 200:

                    st.success(
                        response.json().get(
                            "message",
                            "Student Updated Successfully"
                        )
                    )

                    del st.session_state["student"]

                else:

                    st.error(
                        response.text
                    )


# =================================================
# DELETE STUDENT
# =================================================

elif page == "Delete Student":

    st.title("🗑️ Delete Student")

    student_id = st.number_input(
        "Student ID",
        min_value=1,
        step=1
    )

    st.warning(
        "Deleting a student cannot be undone."
    )

    if st.button(
        "Delete Student",
        type="primary"
    ):

        response = APIClient.delete_student(
            student_id
        )

        if response.status_code == 200:

            st.success(
                response.json().get(
                    "message",
                    "Student Deleted Successfully"
                )
            )

        else:

            st.error(
                response.text
            )