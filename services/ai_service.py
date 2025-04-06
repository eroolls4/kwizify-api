import google.generativeai as genai
import ast
import re
from typing import List, Dict, Any
from core.logging import logger
from core.config import settings

genai.configure(api_key=settings.GOOGLE_API_KEY)


def generate_multiple_choice_questions(keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Generate multiple-choice questions based on keywords using Gemini AI.

    Args:
        keywords (List[str]): List of keywords

    Returns:
        List[dict]: Generated multiple-choice questions
    """
    logger.info(f"Generating questions for keywords: {keywords}")

    if not keywords:
        logger.warning("No keywords provided to generate questions")
        return [{"error": "No keywords provided"}]

    prompt = f"""Generate 5 multiple-choice questions based on these keywords: {', '.join(keywords)}

    Guidelines:
    1. Each question must relate to the keywords
    2. Include:
       - 'question': Full question text
       - 'options': 4 answer options
       - 'correct_answer': Correct option
    3. Ensure educational and challenging questions

    Example format:
    [
      {{
        'question': 'What describes X?',
        'options': ['A', 'B', 'C', 'D'],
        'correct_answer': 'B'
      }}
    ]
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        generation_config = {
            'temperature': 0.7,
            'max_output_tokens': 2048
        }

        logger.info("Sending request to Gemini AI")
        response = model.generate_content(prompt)

        logger.info("Parsing Gemini response")
        # Safer parsing of generated questions by ai
        try:
            questions = ast.literal_eval(response.text)
        except (SyntaxError, ValueError):
            # Fallback parsing
            match = re.search(r'\[.*\]', response.text, re.DOTALL)
            questions = eval(match.group(0)) if match else []

        # Validate questions
        validated_questions = [
            q for q in questions
            if all(key in q for key in ['question', 'options', 'correct_answer'])
        ]

        logger.info(f"Generated {len(validated_questions)} valid questions")
        return validated_questions or [{"error": "No valid questions generated"}]

    except Exception as e:
        logger.error(f"Question generation error: {str(e)}")
        return [{"error": f"Failed to generate questions: {str(e)}"}]