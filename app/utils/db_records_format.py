from typing import Iterable, List, Optional, Union, Tuple, Type
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy import Column
from app import db


# NestedField теперь может принимать InstrumentedAttribute в качестве первого элемента
NestedField = Tuple[
    Union[str, InstrumentedAttribute],
    List[Union[str, Column, InstrumentedAttribute, "NestedField"]]
]


def format_for_chat(
    obj: Union[db.crud.T, Iterable[db.crud.T]],
    *,
    model_fields: Optional[List[Union[
        str,
        Column,
        InstrumentedAttribute,
        NestedField
    ]]] = None,
    field_separator: str = ", ",
    record_separator: str = "\n\n"
) -> str:
    """
    Преобразует одну запись или список записей SQLAlchemy-модели в строку.

    Если передан iterable (список/кортеж) — рекурсивно форматирует каждый элемент
    и склеивает их через record_separator. Иначе форматирует одиночный объект.

    :param obj: Экземпляр модели или iterable таких объектов.
    :param model_fields: Список полей для вывода. Каждый элемент может быть:
           строкой с именем поля, Column, InstrumentedAttribute (например, User.name),
           NestedField = (relation, [subfields...]) для вложенных связей.
           Если None — выводятся все колонки модели.
    :param field_separator: Разделитель между полями в одной записи.
    :param record_separator: Разделитель между записями (для iterable).
    :return: Сформированная строка. Для одного объекта — строка `{field1=..., field2=...}`.
             Для списка — несколько таких блоков, разделённых record_separator.
    """
    # 1) Списки/кортежи (не строки/байты/словарь)
    if isinstance(obj, Iterable) and not isinstance(obj, (str, bytes, dict)):
        formatted = [
            format_for_chat(item, model_fields=model_fields,
                            field_separator=field_separator,
                            record_separator=record_separator)
            for item in obj
        ]
        return record_separator.join(formatted)

    # 2) Словари
    if isinstance(obj, dict):
        items = [f"{k}={v!r}" for k, v in obj.items()]
        return "{ " + field_separator.join(items) + " }"

    # 3) SQLAlchemy‑модель
    if isinstance(obj.__class__, DeclarativeMeta):
        mapper = inspect(obj.__class__)

        flat_fields: List[str] = []
        nested_fields: dict = {}

        if model_fields:
            for mf in model_fields:
                if isinstance(mf, tuple):
                    # вложенная связь
                    key, sub = mf
                    rel_name = key.key if isinstance(key, InstrumentedAttribute) else key
                    nested_fields[rel_name] = sub
                else:
                    # простое поле
                    if isinstance(mf, InstrumentedAttribute):
                        name = mf.key
                    elif isinstance(mf, Column):
                        name = mf.name
                    elif isinstance(mf, str):
                        name = mf
                    else:
                        raise ValueError(f"Unsupported model_field type: {mf!r}")
                    if name not in flat_fields:
                        flat_fields.append(name)

        # если не указали поля — берём все колонки в порядке декларации
        if not flat_fields and not nested_fields:
            flat_fields = [col.key for col in mapper.columns]

        parts: List[str] = []
        # вывод обычных полей в заданном порядке
        for field in flat_fields:
            # пропускаем foreign_key_id, если есть nested для этой связи
            if field.endswith("_id") and field[:-3] in nested_fields:
                continue
            val = getattr(obj, field, None)
            parts.append(f"{field}={val!r}")

        # вывод вложенных связей
        for rel_name, subfields in nested_fields.items():
            if rel_name not in mapper.relationships:
                parts.append(f"{rel_name}=<no relation>")
                continue
            related = getattr(obj, rel_name)
            if related is None:
                parts.append(f"{rel_name}=None")
            else:
                nested = format_for_chat(
                    related,
                    model_fields=subfields,
                    field_separator=field_separator,
                    record_separator=record_separator
                )
                parts.append(f"{rel_name}={nested}")

        return "{ " + field_separator.join(parts) + " }"

    # 4) Примитивы
    return str(obj)


ModelFormatConfig = Tuple[
    Type[db.crud.T],                 # модель
    List[Union[str, Column, InstrumentedAttribute, NestedField]],
    int                              # page size
]


MODEL_FORMATS: List[ModelFormatConfig] = [
    (
        db.ChatType,
        [db.ChatType.id, db.ChatType.type],
        20
    ),
    (
        db.Chat,
        [db.Chat.id, db.Chat.email, (db.Chat.chat_type_model, [db.ChatType.type])],
        20
    ),
    (
        db.User,
        [db.User.id, (db.User.chat, [db.Chat.email]), db.User.first_name, db.User.last_name],
        20
    ),
    (
        db.Group,
        [db.Group.id, (db.Group.chat, [db.Chat.email]), db.Group.title],
        20
    ),
    (
        db.Administrator,
        [
            db.Administrator.user_id,
            (db.Administrator.user, (db.User.chat, [db.Chat.email]), [db.User.first_name, db.User.last_name]),
            db.Administrator.granted_by,
            db.Administrator.granted_at
        ],
        15
    ),
    (
        db.NotificationType,
        [db.NotificationType.id, db.NotificationType.type, db.NotificationType.description],
        20
    ),
    (
        db.NotificationSubscriber,
        [
            db.NotificationSubscriber.id,
            (db.NotificationSubscriber.chat, [db.Chat.email]),
            (db.NotificationSubscriber.notification_type_model, [db.NotificationType.type])
        ],
        20
    ),
]
