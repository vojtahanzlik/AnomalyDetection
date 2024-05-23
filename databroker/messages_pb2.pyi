from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class NumpyArray(_message.Message):
    __slots__ = ("values", "rows", "cols", "id")
    VALUES_FIELD_NUMBER: _ClassVar[int]
    ROWS_FIELD_NUMBER: _ClassVar[int]
    COLS_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[float]
    rows: int
    cols: int
    id: int
    def __init__(self, values: _Optional[_Iterable[float]] = ..., rows: _Optional[int] = ..., cols: _Optional[int] = ..., id: _Optional[int] = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
