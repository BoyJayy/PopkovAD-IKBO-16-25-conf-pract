"""REPL с командами-заглушками для первых этапов задания."""

import getpass
import json
import socket

from parser import parse_command


MAX_PATH_ARGUMENTS = 1
LS_OPTIONS = {"-a", "-l", "-al", "-la"}


def default_prompt():
    """Сформировать приглашение из данных реальной ОС."""
    return f"{getpass.getuser()}@{socket.gethostname()}:~$ "


def validate_arguments(command, arguments):
    """Проверить аргументы поддерживаемых команд."""
    if command == "exit" and arguments:
        raise ValueError("exit не принимает аргументы")
    if command == "cd":
        if len(arguments) > MAX_PATH_ARGUMENTS:
            raise ValueError("cd принимает не более одного пути")
        if arguments and arguments[0].startswith("-"):
            raise ValueError("cd: опции не поддерживаются")
    if command == "vfs-info" and len(arguments) > MAX_PATH_ARGUMENTS:
        raise ValueError("vfs-info принимает не более одного пути")
    if command == "ls":
        for argument in arguments:
            if argument == "--":
                break
            if argument.startswith("-") and argument not in LS_OPTIONS:
                raise ValueError(f"ls: неизвестная опция {argument}")


def execute(line, write=print, vfs=None):
    """Выполнить строку; вернуть True для продолжения диалога."""
    tokens = parse_command(line)
    if not tokens:
        return True
    command, *arguments = tokens
    if command not in ("ls", "cd", "exit", "vfs-info"):
        raise ValueError(f"неизвестная команда: {command}")
    validate_arguments(command, arguments)
    if command == "exit":
        return False
    if command == "vfs-info":
        if vfs is None:
            raise ValueError("VFS не загружена")
        info = vfs.describe(arguments[0] if arguments else "/")
        write("[vfs-info] " + json.dumps(info, ensure_ascii=False))
        return True
    rendered = json.dumps(arguments, ensure_ascii=False)
    write(f"{command}: аргументы = {rendered}")
    return True


def repl(prompt, read=input, write=print, vfs=None):
    """Читать команды до exit или конца ввода, сообщая об ошибках."""
    while True:
        try:
            line = read(prompt)
        except EOFError:
            return
        except KeyboardInterrupt:
            write("")
            continue
        try:
            if not execute(line, write, vfs):
                return
        except ValueError as error:
            write(f"Ошибка: {error}")
