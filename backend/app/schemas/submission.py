"""
StandupBot — Submission Schemas

Request/response schemas for standup form and submissions.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AnswerSubmit(BaseModel):
    """A single answer within a standup submission."""

    question_id: UUID = Field(..., description="ID of the question being answered")
    answer_text: str = Field(..., min_length=1, max_length=5000, description="Answer text")


class SubmissionCreateRequest(BaseModel):
    """Request body for submitting a standup."""

    answers: list[AnswerSubmit] = Field(..., min_length=1, description="List of answers")


class StandupFormResponse(BaseModel):
    """Response for loading the standup form (validates token and returns questions)."""

    team_name: str
    member_name: str
    standup_date: date
    questions: list[dict] = Field(..., description="List of questions with id and text")
    already_submitted: bool = False


class AnswerResponse(BaseModel):
    """Answer detail within a submission response."""

    question_id: UUID
    question_text: str
    answer_text: str

    model_config = {"from_attributes": True}


class SubmissionResponse(BaseModel):
    """Submission detail response."""

    id: UUID
    member_id: UUID
    member_name: str
    standup_date: date
    is_late: bool
    submitted_at: datetime
    answers: list[AnswerResponse] = []

    model_config = {"from_attributes": True}


class SubmissionConfirmation(BaseModel):
    """Confirmation response after successful submission."""

    message: str = "Your standup has been submitted successfully!"
    standup_date: date
    submitted_at: datetime
