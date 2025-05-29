from typing import Dict


def format_json_to_str(data: Dict, indent: int = 0) -> str:
    """
    Форматирует словарь в текст.
    Учитывает вложенность.

    :param data: Форматируемый словарь.
    :param indent: Количество отступов слоёв значений.
    :return: Отформатированный словарь в виде строки.
    """
    lines = []
    indent_str = '  ' * indent  # отступ для вложенности

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{indent_str}{key}:")
                lines.append(format_json_to_str(value, indent + 1))
            else:
                value_str = str(value).replace("\\n", "\n")
                lines.append(f"{indent_str}{key}: {value_str}")
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            lines.append(f"{indent_str}- {format_json_to_str(item, indent + 1).strip()}")
    else:
        value_str = str(data).replace("\\n", "\n")
        lines.append(f"{indent_str}{value_str}")

    return "\n".join(lines)
