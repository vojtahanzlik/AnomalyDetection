from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class AnomalyDetResponse(_message.Message):
    __slots__ = ("id", "result", "series_len", "msg_id")
    ID_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    SERIES_LEN_FIELD_NUMBER: _ClassVar[int]
    MSG_ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    result: bool
    series_len: int
    msg_id: int
    def __init__(self, id: _Optional[int] = ..., result: bool = ..., series_len: _Optional[int] = ..., msg_id: _Optional[int] = ...) -> None: ...

class NumpyArray(_message.Message):
    __slots__ = ("values", "rows", "cols", "msg_id")
    VALUES_FIELD_NUMBER: _ClassVar[int]
    ROWS_FIELD_NUMBER: _ClassVar[int]
    COLS_FIELD_NUMBER: _ClassVar[int]
    MSG_ID_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[float]
    rows: int
    cols: int
    msg_id: int
    def __init__(self, values: _Optional[_Iterable[float]] = ..., rows: _Optional[int] = ..., cols: _Optional[int] = ..., msg_id: _Optional[int] = ...) -> None: ...

class Response(_message.Message):
    __slots__ = ("message",)
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...
