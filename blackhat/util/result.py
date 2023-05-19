from typing import Generic, TypeVar, Optional, Union, Type
from aenum import Enum, skip


class ResultMessage(Enum):
    SUCCESS = "Success"

    @skip
    class FS(Enum):
        PATH_NOT_FOUND = "File/directory not found"
        NOT_ALLOWED_READ = "Not allowed to read"


T = TypeVar("T")


class Result(Generic[T]):
    def __init__(self, success: bool, data: Optional[T] = None,
                 # TODO: Figure out how to typehint this
                 message=None):
        self._success: bool = success
        self._data: Optional[T] = data
        self._message: Optional[ResultMessage] = message

        if success and message is not None:
            self._message = ResultMessage.SUCCESS

    @property
    def success(self) -> bool:
        return self._success

    @property
    def failed(self) -> bool:
        return not self._success

    @property
    def data(self) -> Optional[T]:
        return self._data

    @property
    def message(self) -> Optional[ResultMessage]:
        return self._message

    def has_message(self) -> bool:
        return self._message is not None

    def has_data(self) -> bool:
        return self._data is not None

    def _eq_(self, other):
        if isinstance(other, Result):
            return self.success == other.success and self.data == other.data and self.message == other.message
        return False

    def __repr__(self):
        return f"Result(success={self.success}, data={self.data}, message={self.message})"

    def __str__(self):
        return self.__repr__()
