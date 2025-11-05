import random

from src import logger
from src.db.schemas import TGameBoardState


BOARD_SIZE = 10
SHIPS = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]


def _can_place_ship(
    board:     TGameBoardState,
    x:         int,
    y:         int,
    size:      int,
    direction: int,
) -> bool:
    """
        Проверка возможности размещения корабля.
        Корабли не должны соприкасаться даже углами.

        :param board:      Игровая доска
        :param x:          Координата X начальной точки
        :param y:          Координата Y начальной точки
        :param size:       Размер корабля
        :param direction:  Направление (0 - горизонтально, 1 - вертикально)
        :return:           True, если корабль можно разместить, иначе False
    """
    # Проверка самого корабля и окружающих клеток
    for i in range(size):
        if direction == 0:  # Горизонтально
            check_x, check_y = x + i, y
        else:  # Вертикально
            check_x, check_y = x, y + i

        # Проверка клетки и всех соседних (8 направлений + сама клетка)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = check_x + dx, check_y + dy

                if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                    if board[ny][nx] != 0:
                        return False

    return True


def _place_ship(
    board:     TGameBoardState,
    x:         int,
    y:         int,
    size:      int,
    direction: int,
    ship_id:   int
):
    """
        Размещение корабля на доске

        :param board:      Игровая доска
        :param x:          Координата X начальной точки
        :param y:          Координата Y начальной точки
        :param size:       Размер корабля
        :param direction:  Направление (0 - горизонтально, 1 - вертикально)
        :param ship_id:    Идентификатор корабля
    """

    for i in range(size):
        if direction == 0:  # Горизонтально
            board[y][x + i] = ship_id

        else:  # Вертикально
            board[y + i][x] = ship_id


def generate_random_board() -> TGameBoardState:
    """
    Генерация случайной доски с кораблями по правилам.
    0 - пустая клетка
    Иначе - номер корабля

    :return: Сгенерированная доска
    """

    board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    for ship_id, ship_size in enumerate(SHIPS, start=1):
        placed = False
        attempts = 0
        max_attempts = 1000

        while not placed and attempts < max_attempts:
            attempts += 1

            # Случайное направление (0 - горизонтально, 1 - вертикально)
            direction = random.randint(0, 1)

            if direction == 0:  # Горизонтально
                x = random.randint(0, BOARD_SIZE - ship_size)
                y = random.randint(0, BOARD_SIZE - 1)

                if _can_place_ship(board, x, y, ship_size, direction):
                    _place_ship(board, x, y, ship_size, direction, ship_id)
                    placed = True
            else:  # Вертикально
                x = random.randint(0, BOARD_SIZE - 1)
                y = random.randint(0, BOARD_SIZE - ship_size)

                if _can_place_ship(board, x, y, ship_size, direction):
                    _place_ship(board, x, y, ship_size, direction, ship_id)
                    placed = True

        if not placed:
            logger.error(f"Не удалось разместить корабль {ship_id} после {max_attempts} попыток")
            return generate_random_board()

    logger.info("Генерация игрового поля выполнена успешно")
    return board


__all__ = [
    'generate_random_board'
]
