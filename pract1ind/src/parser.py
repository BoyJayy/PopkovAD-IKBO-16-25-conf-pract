"""Разбор команд с раскрытием переменных окружения без запуска ОС."""

import os
import re


VARIABLE = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|"
                      r"([A-Za-z_][A-Za-z0-9_]*))")


def read_variable(line, index):
    """Вернуть значение переменной и позицию следующего символа."""
    match = VARIABLE.match(line, index)
    if match is None:
        return "$", index + 1
    name = match.group(1) or match.group(2)
    return os.environ.get(name, ""), match.end()


def read_word_part(line, index, quote):
    """Прочитать обычный символ, экранирование или переменную."""
    char = line[index]
    if char == "\\" and quote != "'":
        index += 1
        if index == len(line):
            raise ValueError("обратная косая черта без символа")
        return line[index], index + 1
    if char == "$" and quote != "'":
        return read_variable(line, index)
    return char, index + 1


def read_word(line, index):
    """Прочитать аргумент до пробельного символа вне кавычек."""
    word = []
    quote = None
    while index < len(line):
        char = line[index]
        if quote is None and char.isspace():
            break
        if char in ("'", '"') and quote in (None, char):
            quote = char if quote is None else None
            index += 1
        else:
            value, index = read_word_part(line, index, quote)
            word.append(value)
    if quote is not None:
        raise ValueError("незакрытые кавычки")
    return "".join(word), index


def parse_command(line):
    """Разделить строку и раскрыть $NAME вне одинарных кавычек."""
    tokens = []
    index = 0
    while index < len(line):
        if line[index].isspace():
            index += 1
        else:
            token, index = read_word(line, index)
            tokens.append(token)
    return tokens
