from fastapi import APIRouter, File, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from core.logging import logger
from services.ai_service import generate_multiple_choice_questions
from models.database import get_db, Question, QuestionOption, Quiz, User
from services.auth_service import get_current_user

router = APIRouter()


@router.post("/generate-questions/", response_model=List[dict])
async def generate_questions_endpoint(
        keywords: List[str] = File(...),
        current_user: User = Depends(get_current_user)
):
    """
    Endpoint to generate questions from provided keywords.

    Args:
        keywords (List[str]): List of keywords

    Returns:
        List[dict]: Generated multiple-choice questions
    """
    if current_user is None:
        raise HTTPException(status_code=403, detail="Not authorized to access this user's quizzes")

    logger.info(f"Received keywords: {keywords}")

    if not keywords:
        raise HTTPException(status_code=400, detail="Keywords list cannot be empty")

    questions = generate_multiple_choice_questions(keywords)
    return questions


@router.get("/quiz/{quiz_id}", response_model=dict)
async def get_quiz_endpoint(
        quiz_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
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

    if current_user.id != quiz.creator_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this quiz")

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
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Get all quizzes created by a user.

    Args:
        user_id (int): ID of the user
        db (Session): Database session

    Returns:
        List[dict]: List of quizzes
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this user's quizzes")

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


@router.delete("/quiz/{quiz_id}", response_model=dict)
async def delete_quiz_endpoint(
        quiz_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Delete a quiz by ID.

    Args:
        quiz_id (int): ID of the quiz to delete
        db (Session): Database session
        current_user (User): Current authenticated user

    Returns:
        dict: Success message
    """
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Verify user can only delete their own quizzes
    if current_user.id != quiz.creator_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this quiz")

    try:
        # Delete the quiz and all related questions and options (cascading)
        db.delete(quiz)
        db.commit()

        return {"message": "Quiz deleted successfully", "id": quiz_id}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting quiz: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete quiz: {str(e)}"
        )