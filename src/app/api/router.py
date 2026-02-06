from fastapi import APIRouter
from src.app.api.text2sql_lg_code import router as text2sql_lg_code_router


api_router = APIRouter()

api_router.include_router(text2sql_lg_code_router, prefix="/text2sql_lg_code", tags=["Text2SQL_API"])
