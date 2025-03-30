from fastapi import APIRouter
from api.routes.keywords import router as keywords_router
from api.routes.questions import router as questions_router

router = APIRouter()

router.include_router(keywords_router, prefix="/keywords", tags=["keywords"])
router.include_router(questions_router, prefix="/questions", tags=["questions"])