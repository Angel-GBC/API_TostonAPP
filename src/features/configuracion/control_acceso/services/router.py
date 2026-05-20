from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.shared.services.database import get_db

router = APIRouter()
