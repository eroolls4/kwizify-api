from datetime import datetime

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models.database import *

router = APIRouter()



@router.post("/quiz-attempts/start", response_model=dict)
async def start_quiz_attempt(
        quiz_id: int,
        user_id: int,
        db: Session = Depends(get_db)
):
    """
    Start a new quiz attempt for a user.

    Args:
        quiz_id (int): ID of the quiz
        user_id (int): ID of the user
        db (Session): Database session

    Returns:
        dict: Quiz attempt ID and started_at timestamp
    """
    # Verify quiz exists
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create new attempt
    attempt = QuizAttempt(
        quiz_id=quiz_id,
        user_id=user_id,
        started_at=datetime.utcnow()
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return {
        "attempt_id": attempt.id,
        "started_at": attempt.started_at
    }


@router.post("/quiz-attempts/submit", response_model=dict)
async def submit_quiz_attempt(
        quiz_id: int,
        user_id: int,
        time_spent_seconds: float,
        selected_options: List[str],  # ["A", "C", "B", "D"]
        db: Session = Depends(get_db)
):
    """
    Submit quiz attempt with selected options ("A", "B", "C", "D").
    Assumes the quiz has exactly 4 multiple-choice questions.
    """
    # Validate quiz
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Get questions in order
    questions = db.query(Question).filter(Question.quiz_id == quiz_id).order_by(Question.id).all()

    if len(questions) != len(selected_options):
        raise HTTPException(
            status_code=400,
            detail=f"Number of selected options ({len(selected_options)}) does not match number of questions ({len(questions)})"
        )

    # Create quiz attempt
    attempt = QuizAttempt(
        quiz_id=quiz_id,
        user_id=user_id,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        time_spent_seconds=time_spent_seconds
    )
    db.add(attempt)
    db.flush()

    correct_count = 0

    for i, question in enumerate(questions):
        selected_letter = selected_options[i].upper()
        option_index = ord(selected_letter) - ord('A')

        # Get options for this question ordered by ID (A = 0th, B = 1st, etc.)
        options = db.query(QuestionOption).filter(
            QuestionOption.question_id == question.id
        ).order_by(QuestionOption.id).all()

        if 0 <= option_index < len(options):
            selected_option = options[option_index]

            is_correct = selected_option.is_correct
            if is_correct:
                correct_count += 1

            db.add(QuestionAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_option_id=selected_option.id,
                is_correct=is_correct
            ))
        else:
            db.add(QuestionAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_option_id=None,
                is_correct=False
            ))

    score = (correct_count / len(questions)) * 100

    attempt.score = score
    db.commit()
    db.refresh(attempt)

    return {
        "attempt_id": attempt.id,
        "score": score,
        "correct_answers": correct_count,
        "total_questions": len(questions),
        "time_spent_seconds": time_spent_seconds
    }

@router.get("/quiz-attempts/user/{user_id}", response_model=List[dict])
async def get_user_quiz_attempts(
        user_id: int,
        db: Session = Depends(get_db)
):
    """
    Get all quiz attempts for a user.

    Args:
        user_id (int): ID of the user
        db (Session): Database session

    Returns:
        List[dict]: List of quiz attempts with scores
    """
    attempts = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == user_id
    ).order_by(QuizAttempt.started_at.desc()).all()

    result = []
    for attempt in attempts:
        quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()

        result.append({
            "attempt_id": attempt.id,
            "quiz_id": attempt.quiz_id,
            "quiz_title": quiz.title if quiz else "Unknown",
            "started_at": attempt.started_at,
            "completed_at": attempt.completed_at,
            "time_spent_seconds": attempt.time_spent_seconds,
            "score": attempt.score
        })

    return result


@router.get("/quiz-attempts/{attempt_id}", response_model=dict)
async def get_quiz_attempt_details(
        attempt_id: int,
        db: Session = Depends(get_db)
):
    """
    Get detailed information about a quiz attempt including selected answers.

    Args:
        attempt_id (int): ID of the quiz attempt
        db (Session): Database session

    Returns:
        dict: Detailed quiz attempt information
    """
    attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz attempt not found")

    # Get quiz details
    quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()

    # Get answers with question and option details
    answers = db.query(QuestionAnswer).filter(
        QuestionAnswer.attempt_id == attempt_id
    ).all()

    answers_data = []
    for answer in answers:
        question = db.query(Question).filter(Question.id == answer.question_id).first()

        # Get all options for this question
        options = db.query(QuestionOption).filter(
            QuestionOption.question_id == answer.question_id
        ).order_by(QuestionOption.id).all()

        # Find selected option letter (A, B, C, D)
        selected_letter = None
        if answer.selected_option_id:
            for i, opt in enumerate(options):
                if opt.id == answer.selected_option_id:
                    selected_letter = chr(ord('A') + i)
                    break

        # Find correct option letter
        correct_letter = None
        for i, opt in enumerate(options):
            if opt.is_correct:
                correct_letter = chr(ord('A') + i)
                break

        # Format options
        options_data = [{"id": opt.id, "text": opt.option_text, "is_correct": opt.is_correct} for opt in options]

        answers_data.append({
            "question_id": question.id,
            "question_text": question.question_text if question else "Unknown",
            "selected_option_id": answer.selected_option_id,
            "selected_option_letter": selected_letter,
            "correct_option_letter": correct_letter,
            "is_correct": answer.is_correct,
            "options": options_data
        })

    return {
        "attempt_id": attempt.id,
        "quiz_id": attempt.quiz_id,
        "quiz_title": quiz.title if quiz else "Unknown",
        "user_id": attempt.user_id,
        "started_at": attempt.started_at,
        "completed_at": attempt.completed_at,
        "time_spent_seconds": attempt.time_spent_seconds,
        "score": attempt.score,
        "answers": answers_data
    }