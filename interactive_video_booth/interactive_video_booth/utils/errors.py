from dataclasses import dataclass


@dataclass
class StageError(Exception):
    code: int
    message: str

    def __str__(self) -> str:
        return f"StageError(code={self.code}): {self.message}"
