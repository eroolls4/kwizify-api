import spacy
from typing import List
from core.logging import logger

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("spaCy model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load spaCy model: {e}")
    raise

def extract_keywords(text: str) -> List[str]:
    """
    Extract unique keywords from the given text using spaCy.

    Args:
        text (str): Input text to extract keywords from

    Returns:
        List[str]: List of unique keywords
    """
    logger.info(f"Extracting keywords from text (length: {len(text)} chars)")
    doc = nlp(text)
    logger.info(f"spaCy tokens found: {len(doc)}")

    keywords = [
        token.text.lower()
        for token in doc
        if token.pos_ in ["NOUN", "PROPN", "ADJ"]
           and not token.is_stop
           and not token.is_punct
           and len(token.text) > 2
    ]
    seen = set()
    unique_keywords = [word for word in keywords if not (word in seen or seen.add(word))]

    logger.info(f"Extracted unique keywords: {unique_keywords}")
    return unique_keywords