from typing import List
from fastapi import APIRouter
from sqlalchemy import select, or_, and_

from src.db.models import Player, Game
from src.db.enums import GameStatus

from src.api.dependencies import (
    get_db,
    AsyncSession,
    HTTPException,
    Depends,
    status,
    get_current_player
)

from src.db.schemas import (
    PlayerCreateSchema,
    PlayerLoginSchema,
    PlayerResponseSchema,
    PlayerStatsSchema,
    GameResultSchema
)

from src.db.repositories import (
    PlayerRepository,
    GameRepository
)

from src import logger
from src.schemas.auth import TokenSchema
from src.services.auth import create_access_token, verify_password, get_password_hash


api_players_router = APIRouter(prefix="/players", tags=["Сервис управления игроками"])


@api_players_router.post("/register", response_model=TokenSchema, status_code=status.HTTP_201_CREATED)
async def register_player(
    player_data: PlayerCreateSchema,
    db: AsyncSession = Depends(get_db)
):
    """
        Регистрация нового игрока

        :param player_data: Данные игрока
        :param db:          Сессия БД

        :return:            Токен авторизации
    """

    logger.info(f"Начало регистрации Игрока: {player_data.username}")

    players_repo = PlayerRepository(session=db)

    existing_player = await players_repo.get_one_or_none(
        Player.username == player_data.username
    )

    if existing_player:
        logger.warning(f"Игрок с таким именем уже существует: {player_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Игрок с таким именем уже существует"
        )

    # Создание нового игрока
    player = Player(
        username=player_data.username,
        hashed_password=get_password_hash(player_data.password)
    )

    player = await players_repo.add(player, auto_commit=True, auto_refresh=True)

    # Создание токена
    access_token = create_access_token(data={"sub": player.id})

    logger.info(f"Игрок успешно зарегистрирован: {player.id}")

    return TokenSchema(
        access_token=access_token,
        player=PlayerResponseSchema.model_validate(player)
    )


@api_players_router.post("/login", response_model=TokenSchema)
async def login_player(
    login_data: PlayerLoginSchema,
    db: AsyncSession = Depends(get_db)
):
    """
        Авторизация игрока

        :param login_data: Данные для авторизации
        :param db:         Сессия БД
        :return:           Токен авторизации
    """

    logger.info(f"Начало авторизации пользователя: {login_data.username}")

    players_repo = PlayerRepository(session=db)

    player = await players_repo.get_one_or_none(
        Player.username == login_data.username
    )

    if not player or not verify_password(login_data.password, player.hashed_password):
        logger.warning(f"Неверный пароль или имя пользователя при авторизации пользователя: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный пароль или имя пользователя"
        )

    access_token = create_access_token(data={"sub": player.id})

    logger.info(f"Player logged in successfully: {player.id}")

    return TokenSchema(
        access_token=access_token,
        player=PlayerResponseSchema.model_validate(player)
    )


@api_players_router.get("", response_model=List[PlayerResponseSchema])
async def get_available_players(
    current_player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db)
):
    """
        Получение всех доступных игроков (не в активной игре)

        :param current_player: Текущий игрок
        :param db:             Сессия БД

        :return:               Список доступных игроков
    """

    logger.info(f"Получение доступных игроков: {current_player.id}")

    # Подзапрос для получения игроков, у которых есть активные игры
    subquery = (
        select(Game.player1_id)
        .where(
            Game.status.in_([GameStatus.WAITING, GameStatus.IN_PROGRESS])
        )
        .union(
            select(Game.player2_id)
            .where(
                Game.status.in_([GameStatus.WAITING, GameStatus.IN_PROGRESS])
            )
        )
    )

    # Получение всех игроков, кроме текущего и игроков с активными играми
    result = await db.execute(
        select(Player).where(
            and_(
                Player.id.not_in(subquery),
                Player.id != current_player.id
            )
        )
    )
    available_players = result.scalars().all()

    logger.info(f"Найдено {len(available_players)} доступных игроков")

    return [PlayerResponseSchema.model_validate(p) for p in available_players]


@api_players_router.get("/{player_sid}/stats", response_model=PlayerStatsSchema)
async def get_player_stats(
    player_id: str,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    """
        Получение статистики игрока

        :param player_id: ID игрока
        :param db:        Сессия БД

        :return:          Статистика игрока
    """
    logger.info(f"Получение статистики игр для игрока: {player_id}")

    # Получение игрока
    players_repo = PlayerRepository(session=db)
    player = await players_repo.get_one_or_none(
        Player.id == player_id
    )

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Игрок не найден"
        )

    # Получение всех игр игрока
    games_repo = GameRepository(session=db)

    games = await games_repo.list(
        or_(
            Game.player1_id == player.id,
            Game.player2_id == player.id
        ),
        order_by=Game.created_at.desc()
    )

    # Подсчет статистики
    total_games = len([g for g in games if g.status == GameStatus.FINISHED])
    wins = len([g for g in games if g.winner_id == player.id])
    losses = total_games - wins

    # Формирование списка игр
    game_results = []
    for game in games:
        if game.status == GameStatus.FINISHED:
            opponent = game.player2 if game.player1_id == player.id else game.player1
            result_str = "win" if game.winner_id == player.id else "loss"

            game_results.append(GameResultSchema(
                game_id=game.id,
                opponent_username=opponent.username,
                result=result_str,
                created_at=game.created_at,
                finished_at=game.finished_at
            ))

    logger.info(f"Статистика по игроку {player_id}: {wins} побед, {losses} поражений")

    return PlayerStatsSchema(
        player=PlayerResponseSchema.model_validate(player),
        total_games=total_games,
        wins=wins,
        losses=losses,
        games=game_results
    )


__all__ = [
    'api_players_router'
]
