import uuid

from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src import logger
from src.db.models import Game, GameBoard
from src.db.repositories import GameBoardRepository


async def process_move(
    db:   AsyncSession,
    game: Game,
    x:    int,
    y:    int,
    target_player_id: uuid.UUID,
) -> Tuple[bool, bool]:
    """
        Обработка хода игрока.

        :param db:   Асинхронная сессия базы данных
        :param game: Текущая игра
        :param x:    Координата X выстрела
        :param y:    Координата Y выстрела
        :param target_player_id: ID игрока, по доске которого производится выстрел

        :return: Tuple[<попадание>, <потопление корабля>]
    """
    logger.info(f"Начат процесс ходя для игры {game.id} на клетку ({x}, {y})")

    # Получение доски противника
    game_board_repo = GameBoardRepository(session=db)

    target_board = await game_board_repo.get_one_or_none(
        GameBoard.game_id == game.id,
        GameBoard.player_id == target_player_id
    )

    if not target_board:
        logger.error(f"Игровая доска для пользователя {target_player_id} не найдена")
        return False, False

    # Проверка валидности хода
    if x < 0 or x >= 10 or y < 0 or y >= 10:
        logger.warning(f"Некорректные координаты для хода: ({x}, {y})")
        return False, False

    if target_board.shots_record[y][x]:
        logger.warning(f"Ход на данной ячейке: ({x}, {y}) был совершен ранее")
        return False, False

    # Отметка выстрела
    target_board.shots_record[y][x] = True

    # Проверка попадания
    cell_value = target_board.board_state[y][x]
    hit = cell_value > 0

    sunk = False

    if hit:
        logger.info(f"Нанесен урон кораблю {cell_value} на клетке ({x}, {y})!")

        # Проверка, потоплен ли корабль
        ship_id = cell_value
        ship_cells = []

        for row_idx, row in enumerate(target_board.board_state):
            for col_idx, cell in enumerate(row):
                if cell == ship_id:
                    ship_cells.append((col_idx, row_idx))

        # Проверка, все ли клетки корабля подбиты
        all_hit = all(target_board.shots_record[cy][cx] for cx, cy in ship_cells)

        if all_hit:
            sunk = True
            target_board.ships_remaining -= 1
            logger.info(f"Корабль {ship_id} Подбит! Осталось кораблей: {target_board.ships_remaining}")
    else:
        logger.info(f"Промах по клетке ({x}, {y})")

    await db.commit()

    return hit, sunk


async def check_winner(db: AsyncSession, game: Game) -> Optional[uuid.UUID]:
    """
        Проверка победителя.

        :param db: Асинхронная сессия базы данных
        :param game: Текущая игра

        :return: ID победителя или None, если победитель не найден
    """

    game_board_repo = GameBoardRepository(session=db)

    boards = await game_board_repo.list(
        GameBoard.game_id == game.id
    )

    for board in boards:
        if board.ships_remaining == 0:
            # Победитель - противник этого игрока
            winner_id = game.player2_id if board.player_id == game.player1_id else game.player1_id
            logger.info(f"Победитель найден: {winner_id}")
            return winner_id

    return None


__all__ = [
    'process_move',
    'check_winner'
]
