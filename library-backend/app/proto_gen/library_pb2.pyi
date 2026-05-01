from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class BookStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BOOK_STATUS_UNSPECIFIED: _ClassVar[BookStatus]
    BOOK_STATUS_AVAILABLE: _ClassVar[BookStatus]
    BOOK_STATUS_BORROWED: _ClassVar[BookStatus]
    BOOK_STATUS_RESERVED: _ClassVar[BookStatus]
    BOOK_STATUS_LOST: _ClassVar[BookStatus]

class TransactionStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TRANSACTION_STATUS_UNSPECIFIED: _ClassVar[TransactionStatus]
    TRANSACTION_STATUS_BORROWED: _ClassVar[TransactionStatus]
    TRANSACTION_STATUS_RETURNED: _ClassVar[TransactionStatus]
    TRANSACTION_STATUS_OVERDUE: _ClassVar[TransactionStatus]
BOOK_STATUS_UNSPECIFIED: BookStatus
BOOK_STATUS_AVAILABLE: BookStatus
BOOK_STATUS_BORROWED: BookStatus
BOOK_STATUS_RESERVED: BookStatus
BOOK_STATUS_LOST: BookStatus
TRANSACTION_STATUS_UNSPECIFIED: TransactionStatus
TRANSACTION_STATUS_BORROWED: TransactionStatus
TRANSACTION_STATUS_RETURNED: TransactionStatus
TRANSACTION_STATUS_OVERDUE: TransactionStatus

class Author(_message.Message):
    __slots__ = ("author_id", "name")
    AUTHOR_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    author_id: int
    name: str
    def __init__(self, author_id: _Optional[int] = ..., name: _Optional[str] = ...) -> None: ...

class BookCopy(_message.Message):
    __slots__ = ("copy_id", "book_id", "status", "created_at")
    COPY_ID_FIELD_NUMBER: _ClassVar[int]
    BOOK_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    copy_id: int
    book_id: int
    status: BookStatus
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, copy_id: _Optional[int] = ..., book_id: _Optional[int] = ..., status: _Optional[_Union[BookStatus, str]] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class Book(_message.Message):
    __slots__ = ("book_id", "title", "isbn", "published_year", "authors", "copies", "created_at")
    BOOK_ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    ISBN_FIELD_NUMBER: _ClassVar[int]
    PUBLISHED_YEAR_FIELD_NUMBER: _ClassVar[int]
    AUTHORS_FIELD_NUMBER: _ClassVar[int]
    COPIES_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    book_id: int
    title: str
    isbn: str
    published_year: int
    authors: _containers.RepeatedCompositeFieldContainer[Author]
    copies: _containers.RepeatedCompositeFieldContainer[BookCopy]
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, book_id: _Optional[int] = ..., title: _Optional[str] = ..., isbn: _Optional[str] = ..., published_year: _Optional[int] = ..., authors: _Optional[_Iterable[_Union[Author, _Mapping]]] = ..., copies: _Optional[_Iterable[_Union[BookCopy, _Mapping]]] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class Member(_message.Message):
    __slots__ = ("member_id", "name", "email", "phone", "created_at")
    MEMBER_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    PHONE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    member_id: int
    name: str
    email: str
    phone: str
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, member_id: _Optional[int] = ..., name: _Optional[str] = ..., email: _Optional[str] = ..., phone: _Optional[str] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class Fine(_message.Message):
    __slots__ = ("fine_id", "transaction_id", "amount", "paid", "created_at")
    FINE_ID_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    PAID_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    fine_id: int
    transaction_id: int
    amount: float
    paid: bool
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, fine_id: _Optional[int] = ..., transaction_id: _Optional[int] = ..., amount: _Optional[float] = ..., paid: bool = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class BorrowTransaction(_message.Message):
    __slots__ = ("transaction_id", "copy_id", "member_id", "status", "borrow_date", "due_date", "return_date", "fines", "book_title", "member_name")
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    COPY_ID_FIELD_NUMBER: _ClassVar[int]
    MEMBER_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    BORROW_DATE_FIELD_NUMBER: _ClassVar[int]
    DUE_DATE_FIELD_NUMBER: _ClassVar[int]
    RETURN_DATE_FIELD_NUMBER: _ClassVar[int]
    FINES_FIELD_NUMBER: _ClassVar[int]
    BOOK_TITLE_FIELD_NUMBER: _ClassVar[int]
    MEMBER_NAME_FIELD_NUMBER: _ClassVar[int]
    transaction_id: int
    copy_id: int
    member_id: int
    status: TransactionStatus
    borrow_date: _timestamp_pb2.Timestamp
    due_date: _timestamp_pb2.Timestamp
    return_date: _timestamp_pb2.Timestamp
    fines: _containers.RepeatedCompositeFieldContainer[Fine]
    book_title: str
    member_name: str
    def __init__(self, transaction_id: _Optional[int] = ..., copy_id: _Optional[int] = ..., member_id: _Optional[int] = ..., status: _Optional[_Union[TransactionStatus, str]] = ..., borrow_date: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., due_date: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., return_date: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., fines: _Optional[_Iterable[_Union[Fine, _Mapping]]] = ..., book_title: _Optional[str] = ..., member_name: _Optional[str] = ...) -> None: ...

class CreateAuthorRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class UpdateAuthorRequest(_message.Message):
    __slots__ = ("author_id", "name")
    AUTHOR_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    author_id: int
    name: str
    def __init__(self, author_id: _Optional[int] = ..., name: _Optional[str] = ...) -> None: ...

class CreateBookRequest(_message.Message):
    __slots__ = ("title", "isbn", "published_year", "author_ids", "copies_count")
    TITLE_FIELD_NUMBER: _ClassVar[int]
    ISBN_FIELD_NUMBER: _ClassVar[int]
    PUBLISHED_YEAR_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_IDS_FIELD_NUMBER: _ClassVar[int]
    COPIES_COUNT_FIELD_NUMBER: _ClassVar[int]
    title: str
    isbn: str
    published_year: int
    author_ids: _containers.RepeatedScalarFieldContainer[int]
    copies_count: int
    def __init__(self, title: _Optional[str] = ..., isbn: _Optional[str] = ..., published_year: _Optional[int] = ..., author_ids: _Optional[_Iterable[int]] = ..., copies_count: _Optional[int] = ...) -> None: ...

class UpdateBookRequest(_message.Message):
    __slots__ = ("book_id", "title", "isbn", "published_year", "author_ids")
    BOOK_ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    ISBN_FIELD_NUMBER: _ClassVar[int]
    PUBLISHED_YEAR_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_IDS_FIELD_NUMBER: _ClassVar[int]
    book_id: int
    title: str
    isbn: str
    published_year: int
    author_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, book_id: _Optional[int] = ..., title: _Optional[str] = ..., isbn: _Optional[str] = ..., published_year: _Optional[int] = ..., author_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class CreateMemberRequest(_message.Message):
    __slots__ = ("name", "email", "phone")
    NAME_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    PHONE_FIELD_NUMBER: _ClassVar[int]
    name: str
    email: str
    phone: str
    def __init__(self, name: _Optional[str] = ..., email: _Optional[str] = ..., phone: _Optional[str] = ...) -> None: ...

class UpdateMemberRequest(_message.Message):
    __slots__ = ("member_id", "name", "email", "phone")
    MEMBER_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    PHONE_FIELD_NUMBER: _ClassVar[int]
    member_id: int
    name: str
    email: str
    phone: str
    def __init__(self, member_id: _Optional[int] = ..., name: _Optional[str] = ..., email: _Optional[str] = ..., phone: _Optional[str] = ...) -> None: ...

class BorrowRequest(_message.Message):
    __slots__ = ("copy_id", "member_id", "due_date")
    COPY_ID_FIELD_NUMBER: _ClassVar[int]
    MEMBER_ID_FIELD_NUMBER: _ClassVar[int]
    DUE_DATE_FIELD_NUMBER: _ClassVar[int]
    copy_id: int
    member_id: int
    due_date: _timestamp_pb2.Timestamp
    def __init__(self, copy_id: _Optional[int] = ..., member_id: _Optional[int] = ..., due_date: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ReturnRequest(_message.Message):
    __slots__ = ("transaction_id", "fine_per_day")
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    FINE_PER_DAY_FIELD_NUMBER: _ClassVar[int]
    transaction_id: int
    fine_per_day: float
    def __init__(self, transaction_id: _Optional[int] = ..., fine_per_day: _Optional[float] = ...) -> None: ...

class PayFinesRequest(_message.Message):
    __slots__ = ("fine_ids",)
    FINE_IDS_FIELD_NUMBER: _ClassVar[int]
    fine_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, fine_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class AuthorResponse(_message.Message):
    __slots__ = ("author",)
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    author: Author
    def __init__(self, author: _Optional[_Union[Author, _Mapping]] = ...) -> None: ...

class BookResponse(_message.Message):
    __slots__ = ("book",)
    BOOK_FIELD_NUMBER: _ClassVar[int]
    book: Book
    def __init__(self, book: _Optional[_Union[Book, _Mapping]] = ...) -> None: ...

class MemberResponse(_message.Message):
    __slots__ = ("member",)
    MEMBER_FIELD_NUMBER: _ClassVar[int]
    member: Member
    def __init__(self, member: _Optional[_Union[Member, _Mapping]] = ...) -> None: ...

class BookCopyResponse(_message.Message):
    __slots__ = ("copy",)
    COPY_FIELD_NUMBER: _ClassVar[int]
    copy: BookCopy
    def __init__(self, copy: _Optional[_Union[BookCopy, _Mapping]] = ...) -> None: ...

class TransactionResponse(_message.Message):
    __slots__ = ("transaction",)
    TRANSACTION_FIELD_NUMBER: _ClassVar[int]
    transaction: BorrowTransaction
    def __init__(self, transaction: _Optional[_Union[BorrowTransaction, _Mapping]] = ...) -> None: ...

class AuthorListResponse(_message.Message):
    __slots__ = ("total", "authors")
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    AUTHORS_FIELD_NUMBER: _ClassVar[int]
    total: int
    authors: _containers.RepeatedCompositeFieldContainer[Author]
    def __init__(self, total: _Optional[int] = ..., authors: _Optional[_Iterable[_Union[Author, _Mapping]]] = ...) -> None: ...

class BookListResponse(_message.Message):
    __slots__ = ("total", "books")
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    BOOKS_FIELD_NUMBER: _ClassVar[int]
    total: int
    books: _containers.RepeatedCompositeFieldContainer[Book]
    def __init__(self, total: _Optional[int] = ..., books: _Optional[_Iterable[_Union[Book, _Mapping]]] = ...) -> None: ...

class MemberListResponse(_message.Message):
    __slots__ = ("total", "members")
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    MEMBERS_FIELD_NUMBER: _ClassVar[int]
    total: int
    members: _containers.RepeatedCompositeFieldContainer[Member]
    def __init__(self, total: _Optional[int] = ..., members: _Optional[_Iterable[_Union[Member, _Mapping]]] = ...) -> None: ...

class CopyListResponse(_message.Message):
    __slots__ = ("copies",)
    COPIES_FIELD_NUMBER: _ClassVar[int]
    copies: _containers.RepeatedCompositeFieldContainer[BookCopy]
    def __init__(self, copies: _Optional[_Iterable[_Union[BookCopy, _Mapping]]] = ...) -> None: ...

class FineListResponse(_message.Message):
    __slots__ = ("fines",)
    FINES_FIELD_NUMBER: _ClassVar[int]
    fines: _containers.RepeatedCompositeFieldContainer[Fine]
    def __init__(self, fines: _Optional[_Iterable[_Union[Fine, _Mapping]]] = ...) -> None: ...

class TransactionListResponse(_message.Message):
    __slots__ = ("total", "transactions")
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    TRANSACTIONS_FIELD_NUMBER: _ClassVar[int]
    total: int
    transactions: _containers.RepeatedCompositeFieldContainer[BorrowTransaction]
    def __init__(self, total: _Optional[int] = ..., transactions: _Optional[_Iterable[_Union[BorrowTransaction, _Mapping]]] = ...) -> None: ...

class MarkOverdueResponse(_message.Message):
    __slots__ = ("updated_count",)
    UPDATED_COUNT_FIELD_NUMBER: _ClassVar[int]
    updated_count: int
    def __init__(self, updated_count: _Optional[int] = ...) -> None: ...

class ErrorResponse(_message.Message):
    __slots__ = ("status_code", "error", "detail")
    STATUS_CODE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    DETAIL_FIELD_NUMBER: _ClassVar[int]
    status_code: int
    error: str
    detail: str
    def __init__(self, status_code: _Optional[int] = ..., error: _Optional[str] = ..., detail: _Optional[str] = ...) -> None: ...

class LibraryStats(_message.Message):
    __slots__ = ("total_books", "total_copies", "available_copies", "total_members", "active_loans", "overdue_loans", "total_fines_unpaid")
    TOTAL_BOOKS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COPIES_FIELD_NUMBER: _ClassVar[int]
    AVAILABLE_COPIES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_MEMBERS_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_LOANS_FIELD_NUMBER: _ClassVar[int]
    OVERDUE_LOANS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FINES_UNPAID_FIELD_NUMBER: _ClassVar[int]
    total_books: int
    total_copies: int
    available_copies: int
    total_members: int
    active_loans: int
    overdue_loans: int
    total_fines_unpaid: float
    def __init__(self, total_books: _Optional[int] = ..., total_copies: _Optional[int] = ..., available_copies: _Optional[int] = ..., total_members: _Optional[int] = ..., active_loans: _Optional[int] = ..., overdue_loans: _Optional[int] = ..., total_fines_unpaid: _Optional[float] = ...) -> None: ...
