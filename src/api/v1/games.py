from fastapi import APIRouter, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List

from src.api.dependencies import (
    get_db,
    get_current_player,
    HTTPException,
    status,
    Depends
)

from src.db.repositories import (
    PlayerRepository,
    GameRepository,
    GameBoardRepository
)

from src.db.enums import GameStatus
from src.db.models import Player, Game, GameBoard

from src.db.schemas import GameBoardViewSchema, GameCreateSchema, PlayerBoardSchema, GameResponseSchema

from src.services.board_generator import generate_random_board
from src.services.board_visualizer import generate_board_image
from src import logger


api_game_router = APIRouter()


@api_game_router.post("/create", response_model=GameResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_game(
    game_data: GameCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    """
        Создание новой игры

        :param game_data:      Данные для создания игры
        :param db:             Сессия базы данных
        :param current_player: Текущий игрок
        :returns:              Созданная игра
    """

    logger.info(f"Создание игры между {game_data.player1_sid} и {game_data.player2_sid}")

    # Проверка существования игроков
    players_repo = PlayerRepository(session=db)
    players = await players_repo.list(
        or_(
            Player.id == game_data.player1_id,
            Player.id == game_data.player2_id
        )
    )

    if len(players) != 2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Один или оба игрока не найдены"
        )

    player1 = next(p for p in players if p.sid == game_data.player1_sid)
    player2 = next(p for p in players if p.sid == game_data.player2_sid)

    # Проверка активных игр
    games_repo = GameRepository(session=db)

    active_game = await games_repo.get_one_or_none(
        or_(
            Game.player1_id.in_([player1.id, player2.id]),
            Game.player2_id.in_([player1.id, player2.id])
        ),
        Game.status.in_([GameStatus.WAITING, GameStatus.IN_PROGRESS])
    )

    if active_game:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Один из игроков уже находится в активной игре"
        )

    # Создание игры
    game = Game(
        player1_id=player1.id,
        player2_id=player2.id,
        turn_player_id=player1.id,
        status=GameStatus.WAITING
    )

    game = await games_repo.add(game, auto_refresh=True)

    # Генерация досок для обоих игроков
    board1 = generate_random_board()
    board2 = generate_random_board()

    game_board1 = GameBoard(
        game_id=game.id,
        player_id=player1.id,
        board_state=board1,
        shots_record=[[False] * 10 for _ in range(10)],
        ships_remaining=10
    )

    game_board2 = GameBoard(
        game_id=game.id,
        player_id=player2.id,
        board_state=board2,
        shots_record=[[False] * 10 for _ in range(10)],
        ships_remaining=10
    )


    game_boards_repo = GameBoardRepository(session=db)

    await game_boards_repo.add_many([game_board1, game_board2])

    await db.commit()
    await db.refresh(game)

    logger.info(f"Игра успешно создана: {game.id}")

    # Формирование ответа
    boards = [
        PlayerBoardSchema(
            player_id=player1.id,
            board=GameBoardViewSchema(
                board=game_board1.board_state,
                shots_received=game_board1.shots_record,
                ships_remaining=game_board1.ships_remaining
            )
        ),
        PlayerBoardSchema(
            player_id=player2.id,
            board=GameBoardViewSchema(
                board=game_board2.board_state,
                shots_received=game_board2.shots_record,
                ships_remaining=game_board2.ships_remaining
            )
        )
    ]

    return GameResponseSchema(
        id=game.id,
        player1_id=player1.id,
        player2_id=player2.id,
        turn_player_id=player1.id,
        winner_id=None,
        status=game.status,
        created_at=game.created_at,
        started_at=game.started_at,
        finished_at=game.finished_at,
        boards=boards
    )


@api_game_router.get("", response_model=List[GameResponseSchema])
async def get_active_games(
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    """Получение всех активных игр"""
    logger.info("Fetching all active games")

    result = await db.execute(
        select(Game).where(
            Game.status.in_([GameStatus.WAITING, GameStatus.IN_PROGRESS])
        ).order_by(Game.created_at.desc())
    )
    games = result.scalars().all()

    response_games = []
    for game in games:
        # Получение досок
        result = await db.execute(
            select(GameBoard).where(GameBoard.game_id == game.id)
        )
        boards_data = result.scalars().all()

        boards = []
        for board_data in boards_data:
            player_id = game.player1.id if board_data.player_id == game.player1_id else game.player2.id
            boards.append(
                PlayerBoardSchema(
                    player_id=player_id,
                    board=GameBoardSchema(
                        board=board_data.board,
                        shots_received=board_data.shots_received,
                        ships_remaining=board_data.ships_remaining
                    )
                )
            )

        winner_id = None
        if game.winner_id:
            winner_id = game.player1.sid if game.winner_id == game.player1_id else game.player2.sid

        current_turn_id = None
        if game.turn_player_id:
            current_turn_id = game.player1.sid if game.turn_player_id == game.player1_id else game.player2.sid

        response_games.append(
            GameResponseSchema(
                id=game.id,
                player1_id=game.player1.id,
                player2_id=game.player2.id,
                turn_player_id=current_turn_id,
                winner_id=winner_id,
                status=game.status,
                created_at=game.created_at,
                started_at=game.started_at,
                finished_at=game.finished_at,
                boards=boards
            )
        )

    logger.info(f"Found {len(response_games)} active games")

    return response_games


@api_game_router.get("/{game_sid}/board/image")
async def get_board_image(
    game_id: str,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    """
        Получение изображения игрового поля

        :param game_id:        Идентификатор игры
        :param db:             Сессия базы данных
        :param current_player: Текущий игрок

        :return:               Изображение доски в формате PNG
    """
    logger.info(f"Generating board image for game: {game_id}")

    # Получение игры
    games_repo = GameRepository(session=db)
    game = await games_repo.get_one_or_none(Game.id == game_id)

    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Игра не найдена"
        )

    # Проверка, что игрок участвует в игре
    if game.player1_id != current_player.id and game.player2_id != current_player.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не участвуете в этой игре"
        )

    # Получение доски игрока
    game_boards_repo = GameBoardRepository(session=db)

    game_board = await game_boards_repo.get_one_or_none(
        GameBoard.game_id == game.id,
            GameBoard.player_id == current_player.id
    )

    if not game_board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )

    # Генерация изображения
    image_bytes = generate_board_image(
        game_board.board_state,
        game_board.shots_record
    )

    logger.info(f"Сгенерировано изображение игрового поля для игры: {game_id}")

    return Response(content=image_bytes, media_type="image/png")


__all__ = [
    'api_game_router'
]
