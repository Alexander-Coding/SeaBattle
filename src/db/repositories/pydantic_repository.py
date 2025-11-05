import datetime

from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, Type
from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from src.db.models import UUIDBase


TModel = TypeVar('TModel', bound=UUIDBase)
TPydantic = TypeVar('TPydantic', bound=BaseModel)


class PydanticRepository(SQLAlchemyAsyncRepository[TModel], Generic[TModel, TPydantic]):
    """
        Класс для преобразования SQLAlchemy моделей в Pydantic модели и обратно.
    """

    model_type = Type[TModel]
    pydantic_model_type: Type[TPydantic]

    def to_pydantic(self, obj: TModel) -> TPydantic:
        """
            Преобразует весь объект SQLAlchemy в Pydantic модель, включая все поля и вложенные структуры.

            :param obj: Объект SQLAlchemy модели.
            :return:    Экземпляр Pydantic модели.
        """

        return self.pydantic_model_type.model_validate(obj, from_attributes=True)

    def from_pydantic(self, pydantic_obj: TPydantic, db_obj: Optional[TModel] = None) -> TModel:
        """
            Преобразует Pydantic модель обратно в SQLAlchemy объект, заполняя все поля.
            Если db_obj не передан, создаётся новый экземпляр.

            :param pydantic_obj: Экземпляр Pydantic модели.
            :param db_obj:       Опциональный существующий SQLAlchemy объект для обновления.
            :return:             Объект с данными из Pydantic модели.
        """

        if db_obj is None:
            db_obj = self.model_type()

        data = pydantic_obj.model_dump()

        for key, value in data.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)

        return db_obj


__all__ = [
    'PydanticRepository',
]
