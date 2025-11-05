from fastapi import APIRouter

from .players import api_players_router


v1_router = APIRouter(prefix='/v1', tags=['v1'])
v1_router.include_router(api_players_router, tags=['players'])


__all__ = [
    'v1_router',
]

