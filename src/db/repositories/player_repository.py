from src.db.models import Player
from src.db.schemas import PlayerSchema

from .pydantic_repository import PydanticRepository


class PlayerRepository(PydanticRepository[Player, PlayerSchema]):
    """ Репозиторий для работы с игроками """

    model_type = Player
    pydantic_model_type = PlayerSchema


__all__ = [
    'PlayerRepository'
]
