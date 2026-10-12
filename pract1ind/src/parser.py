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


def parse_command(line):
    """Разделить строку; раскрывать $NAME вне одинарных кавычек."""
    tokens, word = [], []
    quote, active, index = None, False, 0
    while index < len(line):
        char = line[index]
        if char == "\\" and quote != "'":
            index += 1
            if index == len(line):
                raise ValueError("обратная косая черта без символа")
            word.append(line[index])
            active = True
        elif char in ("'", '"') and quote in (None, char):
            quote = char if quote is None else None
            active = True
        elif char.isspace() and quote is None:
            if active:
                tokens.append("".join(word))
                word, active = [], False
        elif char == "$" and quote != "'":
            value, index = read_variable(line, index)
            word.append(value)
            active = True
            continue
        else:
            word.append(char)
            active = True
        index += 1
    if quote is not None:
        raise ValueError("незакрытые кавычки")
    if active:
        tokens.append("".join(word))
    return tokens
