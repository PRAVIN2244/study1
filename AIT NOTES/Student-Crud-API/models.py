from pydantic import BaseModel, Field


class Student(BaseModel):
    name: str = Field(..., min_length=3, max_length=15)
    course: str = Field(..., min_length=3, max_length=15)
    fee : float = Field(..., gt=0)



class StudentUpdate(BaseModel):
    name: str = Field(..., min_length=3, max_length=15)
    course: str = Field(..., min_length=3, max_length=15)
    fee : float = Field(..., gt=0)