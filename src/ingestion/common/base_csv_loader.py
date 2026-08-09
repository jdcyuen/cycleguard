from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")

class BaseCsvLoader(
    ABC,
    Generic[T],
):

    @abstractmethod
    def load(
        self,
        csv_file: str,
    ) -> list[T]:
        ...