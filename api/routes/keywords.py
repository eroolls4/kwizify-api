from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from core.logging import logger
from services.nlp_service import extract_keywords
from services.ai_service import generate_multiple_choice_questions
from utils.pdf_utils import extract_text_from_pdf
from models.database import get_db, Quiz, Question, QuestionOption, User
from services.auth_service import get_current_user

router = APIRouter()

@router.post("/extract-keywords/", response_model=dict)
async def extract_keywords_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint to extract keywords from uploaded file.

    Args:
        file (UploadFile): Uploaded file (text or PDF)
        db (Session): Database session

    Returns:
        dict: Extracted keywords and generated questions
    """
    logger.info(f"Received file upload: {file.filename}")

    try:
        # Verify user permission (can only create quizzes for themselves)
        if current_user is None:
            raise HTTPException(status_code=403, detail="Not authorized to create quiz for this user")

        contents = await file.read()
        logger.info(f"File size: {len(contents)} bytes")

        if file.filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(contents)
        else:
            text = contents.decode('utf-8', errors='replace')

        keywords = extract_keywords(text)
        questions = generate_multiple_choice_questions(keywords)

        return {
            "keywords": keywords,
            "questions": questions
        }

    except UnicodeDecodeError:
        logger.error("File decode error")
        raise HTTPException(status_code=400, detail="Invalid file format")

    except Exception as e:
        logger.error(f"Endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        await file.close()

@router.post("/save-quiz/", response_model=dict)
async def save_quiz_endpoint(
    quiz_title: str,
    quiz_description: str,
    user_id: int,
    questions: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Save a generated quiz to the database.

    Args:
        quiz_title (str): Title of the quiz
        quiz_description (str): Description of the quiz
        user_id (int): ID of the user creating the quiz
        questions (List[dict]): List of questions with options
        db (Session): Database session

    Returns:
        dict: Created quiz ID
    """
    try:
        # Verify user permission (can only create quizzes for themselves)
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to create quiz for this user")

        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Create new quiz
        new_quiz = Quiz(
            title=quiz_title,
            description=quiz_description,
            creator_id=user_id
        )
        db.add(new_quiz)
        db.flush()  # Get the ID without committing

        # Add questions and options
        for q_data in questions:
            # Create question
            question = Question(
                quiz_id=new_quiz.id,
                question_text=q_data["question"]
            )
            db.add(question)
            db.flush()

            # Create options
            for i, option_text in enumerate(q_data["options"]):
                is_correct = option_text == q_data["correct_answer"]
                option = QuestionOption(
                    question_id=question.id,
                    option_text=option_text,
                    is_correct=is_correct
                )
                db.add(option)

        db.commit()
        return {"quiz_id": new_quiz.id}

    except Exception as e:
        db.rollback()
        logger.error(f"Error saving quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save quiz: {str(e)}")