"""Compress shell history to retain commands that I care about.

Purpose:
A single script file to manage shell history based on my personal preferences.
An easier way to avoid simple inconveniences like duplicates might be to use
options such as `HIST_IGNORE_DUPS`, `HIST_IGNORE_SPACE`, etc. But I plan to do 
more with this in the future.
*Caution* Use at your own risk.

Copyright 2024 Abhishek Basu
"""

from enum import auto, StrEnum
import os
import re
import shutil
import sys
import time


class ShellType(StrEnum):
    ZSH = auto()
    BASH = auto()


def get_shell_type() -> ShellType:
    """Try to get the type of shell."""
    shell = os.environ.get("SHELL")
    if not shell:
        print("Can't determine type of shell, exiting.")
        sys.exit(1)

    try:
        shellt = ShellType(shell.split("/")[-1])
    except:
        print(f"Unsupported shell type {shell}, exiting.")
        sys.exit(1)

    return shellt


def get_shell_history_file(shellt: ShellType) -> str:
    """Get the history file based on type of shell."""
    filename = None  # TODO: instead use os.environ.get("HISTFILE")?
    if shellt == ShellType.ZSH:
        filename = ".zsh_history"
    elif shellt == ShellType.BASH:
        filename = ".bash_history"
    else:
        raise NotImplementedError()

    file = os.path.expanduser("~")+"/"+filename
    if not os.path.exists(file):
        print("Can't find shell history file, exiting.")
        sys.exit(1)

    return file


def parse_history_entry(entry: str, shellt: ShellType) -> str | None:
    """Try to parse a particular raw entry depending on the shell type. 

    Args:
        entry: A single raw shell history entry.
        shellt: Type of shell.

    Returns:
        None if unable to parse, else the parsed entry.    
    """
    pattern = None
    if shellt == ShellType.ZSH:
        pattern = re.compile(r"(: \d+:\d+;)(.+)")
        match = re.search(pattern, entry)
        if not match:
            return None
        return match.group(2)  # type: ignore
    elif shellt == ShellType.BASH:
        return entry


def filter(parsed_entry: str) -> bool:
    """Filter list to remove commands that I don't care about.

    Args:
        parsed_entry: A single parsed shell history entry.

    Returns:
        True if entry should be retained, False otherwise.
    """
    # TODO: these will be in a separate config later on
    _starts_with = [
        "source",
        "git commit"
    ]

    _editors = [
        "nano",
        "vim",
        "nvim",
        "subl",
        "code",
        "emacs"
    ]

    _exact_match = [
        "python",
        "clear",
        "ls",
        "pwd",
        "cd ~",
        "cd /",
        "cd",
        "cd ..",
        "cd ."
    ]

    keep = True
    if parsed_entry in _exact_match:
        keep = False
    elif parsed_entry in _editors:
        keep = False
    elif sum([parsed_entry.startswith(s) for s in _starts_with]) > 0:
        keep = False

    return keep


def remove_long_commands(parsed_entry: str, command_length: int = 60) -> bool:
    """Remove all commands that are longer than a given length.

    Args:
        parsed_entry: A single parsed shell history entry.
        command_length: The maximum length of commands retained.

    Returns:
        True if entry should be retained, False otherwise.
    """
    keep = True
    if len(parsed_entry) > command_length:
        keep = False
    return keep


def clean_history_file(
    raw_history: list[str],
    shellt: ShellType,
    dedup=True,
) -> list[str]:
    """Clean shell history file.

    Args:
        raw_history: Raw shell history.
        shellt: Type of shell.
        dedup: Retain only the last instance of a command.

    Returns:
        Cleaned shell history.
    """
    results = []
    unparsed = 0
    unique_parsed_entries = set()

    for entry in reversed(raw_history):
        parsed_entry = parse_history_entry(entry, shellt)
        if parsed_entry is None:
            unparsed += 1
        else:
            keep = filter(parsed_entry)
            if not keep:
                continue
            if dedup and (parsed_entry in unique_parsed_entries):
                continue

        results.append(entry)
        unique_parsed_entries.add(parsed_entry)

    results.reverse()
    return results


def main():
    st = get_shell_type()
    history_file = get_shell_history_file(st)
    with open(history_file, "r") as f:
        history = f.readlines()
    cleaned_history = clean_history_file(history, st)
    shutil.copy(history_file, history_file+f".{int(time.time())}.bak")
    with open(history_file, "w") as f:  # TODO: use history -c and -w maybe?
        f.writelines(cleaned_history)


if __name__ == "__main__":
    main()  # add args and parse them
