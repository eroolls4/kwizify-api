from fastapi import APIRouter, File, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from core.logging import logger
from services.ai_service import generate_multiple_choice_questions
from models.database import get_db, Question, QuestionOption, Quiz

router = APIRouter()


@router.post("/generate-questions/", response_model=List[dict])
async def generate_questions_endpoint(
        keywords: List[str] = File(...),
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
        db: Session = Depends(get_db)
):
    """
    Get a quiz by ID with its questions and options.

    Args:
        quiz_id (int): ID of the quiz
        db (Session): Database session

    Returns:
        dict: Quiz with questions and options
    """
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Get questions
    questions_data = []
    questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()

    for question in questions:
        # Get options
        options = db.query(QuestionOption).filter(QuestionOption.question_id == question.id).all()

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
        db: Session = Depends(get_db)
):
    """
    Get all quizzes created by a user.

    Args:
        user_id (int): ID of the user
        db (Session): Database session

    Returns:
        List[dict]: List of quizzes
    """
    quizzes = db.query(Quiz).filter(Quiz.creator_id == user_id).all()

    return [
        {
            "id": quiz.id,
            "title": quiz.title,
            "description": quiz.description,
            "created_at": quiz.created_at,
            "question_count": db.query(Question).filter(Question.quiz_id == quiz.id).count()
        }
        for quiz in quizzes
    ]