from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

from src.db.enums import GameStatus
from src.db.schemas import PlayerBoardSchema, GameBoardSchema


class GameSchema(BaseModel):
    """ Схема модели игры """

    id:             str
    player1_id:     str
    player2_id:     str
    turn_player_id: Optional[str]
    winner_id:      Optional[str]
    status:         GameStatus
    created_at:     datetime
    started_at:     Optional[datetime]
    finished_at:    Optional[datetime]
    updated_at:     Optional[datetime]

    class Config:
        from_attributes = True


class GameCreateSchema(BaseModel):
    """ Модель для создания игры """

    player1_id: str
    player2_id: str


class GameResponseSchema(BaseModel):
    """ Модель ответа с информацией об игре """

    id:             str
    player1_id:     str
    player2_id:     str
    turn_player_id: Optional[str] = None
    winner_id:      Optional[str] = None
    status:         GameStatus
    created_at:     datetime
    started_at:     Optional[datetime] = None
    finished_at:    Optional[datetime] = None
    boards:         List[PlayerBoardSchema]

    class Config:
        from_attributes = True


class GameStatsSchema(BaseModel):
    id:               str
    player1_username: str
    player2_username: str
    winner_username:  Optional[str]
    status:           GameStatus
    created_at:       datetime
    finished_at:      Optional[datetime]


__all__ = [
    'GameSchema',
    'GameCreateSchema',
    'GameResponseSchema',
    'GameStatsSchema'
]
