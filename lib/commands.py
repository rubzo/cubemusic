class Command:
    pass


class CubeCommand(Command):
    def __init__(self, genre: str):
        self._genre = genre

    def get_genre(self) -> str:
        return self._genre


class SkipCommand(Command):
    pass


class UncubeCommand(Command):
    pass


class QuitCommand(Command):
    pass


def parse_command(command_str: str) -> Command:
    parts = command_str.strip().split()
    if not parts:
        raise ValueError("Empty command")

    cmd = parts[0].lower()
    if cmd == "cube":
        if len(parts) != 2:
            raise ValueError("Usage: cube <genre>")
        genre = parts[1]
        return CubeCommand(genre)
    elif cmd == "skip":
        return SkipCommand()
    elif cmd == "uncube":
        return UncubeCommand()
    elif cmd == "quit":
        return QuitCommand()
    else:
        raise ValueError(f"Unknown command: {cmd}")
