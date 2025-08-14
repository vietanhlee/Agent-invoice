from fastapi import APIRouter
from schema.Message import Message
from
router = APIRouter()

@router.on_event("startup")
def startup():


@router.post("/chat")
def chat(message: Message):

from fastapi import APIRouter

router = APIRouter()
