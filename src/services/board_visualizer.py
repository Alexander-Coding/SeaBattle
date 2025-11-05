import io

from PIL import Image, ImageDraw, ImageFont

from src import logger
from src.db.schemas import TGameBoardState, TShotsRecord


CELL_SIZE = 40
BOARD_SIZE = 10
MARGIN = 30
FONT_SIZE = 20


def generate_board_image(board: TGameBoardState, shots: TShotsRecord) -> bytes:
    """
        Генерация изображения игрового поля.
        Синий - корабль
        Красный - попадание
        Серый - промах
        Белый - пустая клетка

        :param board: Состояние игровой доски
        :param shots: Запись выстрелов по доске
        :return:      Изображение в формате PNG в виде байтов
    """

    logger.info("Начата генерация изображения игрового поля")

    # Размеры изображения
    img_width = BOARD_SIZE * CELL_SIZE + 2 * MARGIN
    img_height = BOARD_SIZE * CELL_SIZE + 2 * MARGIN

    # Создание изображения
    img = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(img)

    font = ImageFont.load_default()

    # Отрисовка координат
    for i in range(BOARD_SIZE):
        # Буквы (A-J)
        letter = chr(65 + i)
        draw.text(
            (MARGIN + i * CELL_SIZE + CELL_SIZE // 2 - 5, 5),
            letter,
            fill='black',
            font=font
        )

        # Цифры (1-10)
        number = str(i + 1)
        draw.text(
            (5, MARGIN + i * CELL_SIZE + CELL_SIZE // 2 - 10),
            number,
            fill='black',
            font=font
        )

    # Отрисовка клеток
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            x_pos = MARGIN + x * CELL_SIZE
            y_pos = MARGIN + y * CELL_SIZE

            # Определение цвета клетки
            cell_value = board[y][x]
            is_shot = shots[y][x]

            if is_shot:
                if cell_value > 0:  # Попадание
                    color = 'red'
                else:  # Промах
                    color = 'gray'
            else:
                if cell_value > 0:  # Корабль
                    color = 'blue'
                else:  # Пустая клетка
                    color = 'lightblue'

            # Рисование клетки
            draw.rectangle(
                [x_pos, y_pos, x_pos + CELL_SIZE, y_pos + CELL_SIZE],
                fill=color,
                outline='black',
                width=1
            )

            # Отметка попадания/промаха
            if is_shot:
                if cell_value > 0:
                    # Крестик для попадания
                    draw.line(
                        [x_pos + 5, y_pos + 5, x_pos + CELL_SIZE - 5, y_pos + CELL_SIZE - 5],
                        fill='white',
                        width=3
                    )
                    draw.line(
                        [x_pos + CELL_SIZE - 5, y_pos + 5, x_pos + 5, y_pos + CELL_SIZE - 5],
                        fill='white',
                        width=3
                    )
                else:
                    # Точка для промаха
                    draw.ellipse(
                        [x_pos + CELL_SIZE // 2 - 5, y_pos + CELL_SIZE // 2 - 5,
                         x_pos + CELL_SIZE // 2 + 5, y_pos + CELL_SIZE // 2 + 5],
                        fill='white'
                    )

    # Сохранение в байты
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    logger.info("Изображение игровой доски успешно сгенерировано")

    return img_byte_arr.getvalue()


__all__ = [
    'generate_board_image'
]
