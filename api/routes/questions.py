from fastapi import APIRouter, File, Depends, HTTPException
from typing import List

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse
from sqlalchemy.future import select
from core.logging import logger
from services.ai_service import generate_multiple_choice_questions
from models.database import get_db, Question, QuestionOption, Quiz

router = APIRouter()

@router.post("/generate-questions/", response_model=List[dict])
async def generate_questions_endpoint(
        keywords: List[str],
):
    """
    Endpoint to generate questions from provided keywords.

    Args:
        keywords (List[str]): List of keywords

    Returns:
        List[dict]: Generated multiple-choice questions
    """
    logger.info(f"Received keywords: {keywords}")

    if not keywords:
        raise HTTPException(status_code=400, detail="Keywords list cannot be empty")

    questions = generate_multiple_choice_questions(keywords)
    return questions


@router.get("/quiz/{quiz_id}", response_model=dict)
async def get_quiz_endpoint(
        quiz_id: int,
        db: AsyncSession = Depends(get_db)
):
    """
    Get a quiz by ID with its questions and options.

    Args:
        quiz_id (int): ID of the quiz
        db (AsyncSession): Database session

    Returns:
        dict: Quiz with questions and options
    """
    result = await db.execute(select(Quiz).filter(Quiz.id == quiz_id))
    quiz = result.scalars().first()

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Get questions asynchronously
    result = await db.execute(select(Question).filter(Question.quiz_id == quiz_id))
    questions = result.scalars().all()

    questions_data = []
    for question in questions:
        # Get options asynchronously
        result = await db.execute(select(QuestionOption).filter(QuestionOption.question_id == question.id))
        options = result.scalars().all()

        # Format options
        options_data = [{"id": opt.id, "text": opt.option_text, "is_correct": opt.is_correct} for opt in options]

        questions_data.append({
            "id": question.id,
            "question_text": question.question_text,
            "options": options_data
        })

    return {
        "id": quiz.id,
        "title": quiz.title,
        "description": quiz.description,
        "creator_id": quiz.creator_id,
        "created_at": quiz.created_at,
        "questions": questions_data
    }


@router.get("/user/{user_id}/quizzes", response_model=List[dict])
async def get_user_quizzes_endpoint(
        user_id: int,
        db: AsyncSession = Depends(get_db)
):
    """
    Get all quizzes created by a user.

    Args:
        user_id (int): ID of the user
        db (AsyncSession): Database session

    Returns:
        List[dict]: List of quizzes
    """
    result = await db.execute(select(Quiz).where(Quiz.creator_id == user_id))
    quizzes = result.scalars().all()

    quiz_data = []
    for quiz in quizzes:
        # Get question count asynchronously
        result = await db.execute(
            select(func.count()).filter(Question.quiz_id == quiz.id)
        )
        question_count = result.scalar()

        quiz_data.append({
            "id": quiz.id,
            "title": quiz.title,
            "description": quiz.description,
            "created_at": quiz.created_at,
            "question_count": question_count
        })

    return quiz_data

@router.options("/{path:path}", include_in_schema=False)
async def options_route(path: str):
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type"
        }
    )