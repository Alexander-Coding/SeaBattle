from src.db.models import GameBoard
from src.db.schemas import GameBoardSchema

from .pydantic_repository import PydanticRepository


class GameBoardRepository(PydanticRepository[GameBoard, GameBoardSchema]):
    """ Репозиторий для работы с моделью GameBoard """

    model_type = GameBoard
    pydantic_model_type = GameBoardSchema


__all__ = [
    'GameBoardRepository'
]
