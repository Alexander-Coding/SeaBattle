from src.db.models import Game
from src.db.schemas import GameSchema

from .pydantic_repository import PydanticRepository


class GameRepository(PydanticRepository[Game, GameSchema]):
    """ Репозиторий для работы с играми """

    model_type = Game
    pydantic_model_type = GameSchema


__all__ = [
    'GameRepository'
]
