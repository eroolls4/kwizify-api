from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from typing import List
from core.logging import logger
from services.nlp_service import extract_keywords
from services.ai_service import generate_multiple_choice_questions
from utils.pdf_utils import extract_text_from_pdf
from models.database import get_db, Quiz, Question, QuestionOption, User

router = APIRouter()

@router.post("/extract-keywords/", response_model=dict)
async def extract_keywords_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
):
    """
    Save a generated quiz to the database.
    """
    try:
        # Verify user exists
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Create new quiz
        new_quiz = Quiz(
            title=quiz_title,
            description=quiz_description,
            creator_id=user_id
        )
        db.add(new_quiz)
        await db.flush()  # async flush to get ID

        # Add questions and options
        for q_data in questions:
            question = Question(
                quiz_id=new_quiz.id,
                question_text=q_data["question"]
            )
            db.add(question)
            await db.flush()  # async flush to get question.id

            for option_text in q_data["options"]:
                is_correct = option_text == q_data["correct_answer"]
                option = QuestionOption(
                    question_id=question.id,
                    option_text=option_text,
                    is_correct=is_correct
                )
                db.add(option)

        await db.commit()
        return {"quiz_id": new_quiz.id}

    except Exception as e:
        await db.rollback()
        logger.error(f"Error saving quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save quiz: {str(e)}")