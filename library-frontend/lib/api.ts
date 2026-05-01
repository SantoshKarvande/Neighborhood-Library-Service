import {
  PROTO_CONTENT_TYPE,
  PlainRecord,
  decodeErrorResponse,
  decodeMessage,
  encodeMessage,
  getApiBaseUrl
} from "./protobuf";

export type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE";

export type OperationId =
  | "listAuthors"
  | "getAuthor"
  | "createAuthor"
  | "updateAuthor"
  | "deleteAuthor"
  | "listBooks"
  | "getBook"
  | "createBook"
  | "updateBook"
  | "deleteBook"
  | "listCopies"
  | "addCopies"
  | "updateCopyStatus"
  | "listMembers"
  | "getMember"
  | "createMember"
  | "updateMember"
  | "deleteMember"
  | "listLoans"
  | "getLoan"
  | "borrowBook"
  | "returnBook"
  | "getBorrowedBooks"
  | "getDueBooks"
  | "markOverdue"
  | "getTransactionFines"
  | "getMemberFines"
  | "payFines"
  | "getStats";

export type OperationField = {
  name: string;
  label: string;
  type: "text" | "number" | "datetime-local" | "checkbox" | "select";
  placeholder?: string;
  options?: string[];
  required?: boolean;
  defaultValue?: string | number | boolean;
  help?: string;
};

export type Operation = {
  id: OperationId;
  group: "Authors" | "Books" | "Members" | "Loans" | "Fines" | "Stats";
  label: string;
  method: HttpMethod;
  path: string;
  requestType?: string;
  responseType?: string;
  fields: OperationField[];
  bodyBuilder?: (values: PlainRecord) => PlainRecord;
  queryBuilder?: (values: PlainRecord) => URLSearchParams;
  disabledReason?: string;
};

const paginationFields: OperationField[] = [
  { name: "skip", label: "Skip", type: "number", defaultValue: 0 },
  { name: "limit", label: "Limit", type: "number", defaultValue: 20 }
];

export const operations: Operation[] = [
  {
    id: "listAuthors",
    group: "Authors",
    label: "List authors",
    method: "GET",
    path: "/authors/",
    responseType: "AuthorListResponse",
    fields: [
      ...paginationFields,
      { name: "search", label: "Search", type: "text", placeholder: "name contains" }
    ]
  },
  {
    id: "getAuthor",
    group: "Authors",
    label: "Get author",
    method: "GET",
    path: "/authors/{author_id}",
    responseType: "AuthorResponse",
    fields: [{ name: "author_id", label: "Author ID", type: "number", required: true }]
  },
  {
    id: "createAuthor",
    group: "Authors",
    label: "Create author",
    method: "POST",
    path: "/authors/",
    requestType: "CreateAuthorRequest",
    responseType: "AuthorResponse",
    fields: [{ name: "name", label: "Name", type: "text", required: true }]
  },
  {
    id: "updateAuthor",
    group: "Authors",
    label: "Update author",
    method: "PATCH",
    path: "/authors/{author_id}",
    requestType: "UpdateAuthorRequest",
    responseType: "AuthorResponse",
    fields: [
      { name: "author_id", label: "Author ID", type: "number", required: true },
      { name: "name", label: "Name", type: "text", required: true }
    ],
    bodyBuilder: (v) => ({ author_id: v.author_id, name: v.name })
  },
  {
    id: "deleteAuthor",
    group: "Authors",
    label: "Delete author",
    method: "DELETE",
    path: "/authors/{author_id}",
    fields: [{ name: "author_id", label: "Author ID", type: "number", required: true }]
  },
  {
    id: "listBooks",
    group: "Books",
    label: "List books",
    method: "GET",
    path: "/books/",
    responseType: "BookListResponse",
    fields: [
      ...paginationFields,
      { name: "search", label: "Search", type: "text", placeholder: "title contains" },
      { name: "author_id", label: "Author ID", type: "number" },
      { name: "available_only", label: "Available only", type: "checkbox" }
    ]
  },
  {
    id: "getBook",
    group: "Books",
    label: "Get book",
    method: "GET",
    path: "/books/{book_id}",
    responseType: "BookResponse",
    fields: [{ name: "book_id", label: "Book ID", type: "number", required: true }]
  },
  {
    id: "createBook",
    group: "Books",
    label: "Create book",
    method: "POST",
    path: "/books/",
    requestType: "CreateBookRequest",
    responseType: "BookResponse",
    fields: [
      { name: "title", label: "Title", type: "text", required: true },
      { name: "isbn", label: "ISBN", type: "text", placeholder: "max 20 chars" },
      { name: "published_year", label: "Published year", type: "number" },
      { name: "author_ids", label: "Author IDs", type: "text", placeholder: "1,2" },
      { name: "copies_count", label: "Copies", type: "number", defaultValue: 1 }
    ]
  },
  {
    id: "updateBook",
    group: "Books",
    label: "Update book",
    method: "PATCH",
    path: "/books/{book_id}",
    requestType: "UpdateBookRequest",
    responseType: "BookResponse",
    fields: [
      { name: "book_id", label: "Book ID", type: "number", required: true },
      { name: "title", label: "Title", type: "text" },
      { name: "isbn", label: "ISBN", type: "text" },
      { name: "published_year", label: "Published year", type: "number" },
      { name: "author_ids", label: "Author IDs", type: "text", placeholder: "1,2" }
    ]
  },
  {
    id: "deleteBook",
    group: "Books",
    label: "Delete book",
    method: "DELETE",
    path: "/books/{book_id}",
    fields: [{ name: "book_id", label: "Book ID", type: "number", required: true }]
  },
  {
    id: "listCopies",
    group: "Books",
    label: "List book copies",
    method: "GET",
    path: "/books/{book_id}/copies",
    responseType: "CopyListResponse",
    fields: [
      { name: "book_id", label: "Book ID", type: "number", required: true },
      {
        name: "status",
        label: "Status",
        type: "select",
        options: ["", "AVAILABLE", "BORROWED", "RESERVED", "LOST"]
      }
    ]
  },
  {
    id: "addCopies",
    group: "Books",
    label: "Add copies",
    method: "POST",
    path: "/books/{book_id}/copies",
    responseType: "BookResponse",
    fields: [
      { name: "book_id", label: "Book ID", type: "number", required: true },
      { name: "count", label: "Count", type: "number", defaultValue: 1 }
    ]
  },
  {
    id: "updateCopyStatus",
    group: "Books",
    label: "Update copy status",
    method: "PATCH",
    path: "/books/copies/{copy_id}/status",
    responseType: "BookCopyResponse",
    disabledReason:
      "The backend REST route has a body, but library.proto has no protobuf request message for copy status updates.",
    fields: [
      { name: "copy_id", label: "Copy ID", type: "number", required: true },
      {
        name: "status",
        label: "Status",
        type: "select",
        required: true,
        options: ["AVAILABLE", "BORROWED", "RESERVED", "LOST"]
      }
    ]
  },
  {
    id: "listMembers",
    group: "Members",
    label: "List members",
    method: "GET",
    path: "/members/",
    responseType: "MemberListResponse",
    fields: [
      ...paginationFields,
      { name: "search", label: "Search", type: "text", placeholder: "name or email" }
    ]
  },
  {
    id: "getMember",
    group: "Members",
    label: "Get member",
    method: "GET",
    path: "/members/{member_id}",
    responseType: "MemberResponse",
    fields: [{ name: "member_id", label: "Member ID", type: "number", required: true }]
  },
  {
    id: "createMember",
    group: "Members",
    label: "Create member",
    method: "POST",
    path: "/members/",
    requestType: "CreateMemberRequest",
    responseType: "MemberResponse",
    fields: [
      { name: "name", label: "Name", type: "text", required: true },
      { name: "email", label: "Email", type: "text" },
      { name: "phone", label: "Phone", type: "text" }
    ]
  },
  {
    id: "updateMember",
    group: "Members",
    label: "Update member",
    method: "PATCH",
    path: "/members/{member_id}",
    requestType: "UpdateMemberRequest",
    responseType: "MemberResponse",
    fields: [
      { name: "member_id", label: "Member ID", type: "number", required: true },
      { name: "name", label: "Name", type: "text" },
      { name: "email", label: "Email", type: "text" },
      { name: "phone", label: "Phone", type: "text" }
    ]
  },
  {
    id: "deleteMember",
    group: "Members",
    label: "Delete member",
    method: "DELETE",
    path: "/members/{member_id}",
    fields: [{ name: "member_id", label: "Member ID", type: "number", required: true }]
  },
  {
    id: "listLoans",
    group: "Loans",
    label: "List loans",
    method: "GET",
    path: "/loans/",
    responseType: "TransactionListResponse",
    fields: [
      ...paginationFields,
      { name: "member_id", label: "Member ID", type: "number" },
      { name: "book_id", label: "Book ID", type: "number" },
      {
        name: "status",
        label: "Status",
        type: "select",
        options: ["", "BORROWED", "RETURNED", "OVERDUE"]
      },
      { name: "overdue_only", label: "Overdue only", type: "checkbox" }
    ]
  },
  {
    id: "getLoan",
    group: "Loans",
    label: "Get loan",
    method: "GET",
    path: "/loans/{transaction_id}",
    responseType: "TransactionResponse",
    fields: [{ name: "transaction_id", label: "Transaction ID", type: "number", required: true }]
  },
  {
    id: "borrowBook",
    group: "Loans",
    label: "Borrow book",
    method: "POST",
    path: "/loans/",
    requestType: "BorrowRequest",
    responseType: "TransactionResponse",
    fields: [
      { name: "copy_id", label: "Copy ID", type: "number", required: true },
      { name: "member_id", label: "Member ID", type: "number", required: true },
      { name: "due_date", label: "Due date", type: "datetime-local", required: true }
    ]
  },
  {
    id: "returnBook",
    group: "Loans",
    label: "Return book",
    method: "POST",
    path: "/loans/{transaction_id}/return",
    requestType: "ReturnRequest",
    responseType: "TransactionResponse",
    fields: [
      { name: "transaction_id", label: "Transaction ID", type: "number", required: true },
      { name: "fine_per_day", label: "Fine per day", type: "number", defaultValue: 0.5 }
    ],
    bodyBuilder: (v) => ({ transaction_id: v.transaction_id, fine_per_day: v.fine_per_day })
  },
  {
    id: "getBorrowedBooks",
    group: "Loans",
    label: "Borrowed books",
    method: "GET",
    path: "/loans/borrowed",
    responseType: "TransactionListResponse",
    fields: [...paginationFields, { name: "member_id", label: "Member ID", type: "number" }]
  },
  {
    id: "getDueBooks",
    group: "Loans",
    label: "Due books",
    method: "GET",
    path: "/loans/due",
    responseType: "TransactionListResponse",
    fields: [...paginationFields]
  },
  {
    id: "markOverdue",
    group: "Loans",
    label: "Mark overdue",
    method: "POST",
    path: "/loans/mark-overdue",
    responseType: "MarkOverdueResponse",
    fields: []
  },
  {
    id: "getTransactionFines",
    group: "Fines",
    label: "Transaction fines",
    method: "GET",
    path: "/loans/{transaction_id}/fines",
    responseType: "FineListResponse",
    fields: [{ name: "transaction_id", label: "Transaction ID", type: "number", required: true }]
  },
  {
    id: "getMemberFines",
    group: "Fines",
    label: "Member fines",
    method: "GET",
    path: "/loans/members/{member_id}/fines",
    responseType: "FineListResponse",
    fields: [
      { name: "member_id", label: "Member ID", type: "number", required: true },
      { name: "unpaid_only", label: "Unpaid only", type: "checkbox" }
    ]
  },
  {
    id: "payFines",
    group: "Fines",
    label: "Pay fines",
    method: "POST",
    path: "/loans/fines/pay",
    requestType: "PayFinesRequest",
    responseType: "FineListResponse",
    fields: [{ name: "fine_ids", label: "Fine IDs", type: "text", required: true, placeholder: "1,2" }]
  },
  {
    id: "getStats",
    group: "Stats",
    label: "Library stats",
    method: "GET",
    path: "/loans/stats",
    responseType: "LibraryStats",
    fields: []
  }
];

export function buildRequestBody(operation: Operation, values: PlainRecord): PlainRecord {
  if (operation.bodyBuilder) {
    return operation.bodyBuilder(values);
  }

  const body: PlainRecord = {};
  for (const field of operation.fields) {
    if (operation.path.includes(`{${field.name}}`)) {
      continue;
    }

    const value = values[field.name];
    if (value !== "" && value !== undefined && value !== null) {
      body[field.name] = value;
    }
  }

  return body;
}

export function normalizeFormValues(values: PlainRecord): PlainRecord {
  const result: PlainRecord = {};

  for (const [key, value] of Object.entries(values)) {
    if (typeof value !== "string") {
      result[key] = value;
      continue;
    }

    if (key.endsWith("_ids") || key === "fine_ids") {
      result[key] = value
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean)
        .map(Number);
    } else if (
      [
        "skip",
        "limit",
        "author_id",
        "book_id",
        "copy_id",
        "member_id",
        "transaction_id",
        "published_year",
        "copies_count",
        "count"
      ].includes(key)
    ) {
      result[key] = value === "" ? "" : Number(value);
    } else if (key === "fine_per_day") {
      result[key] = value === "" ? "" : Number(value);
    } else {
      result[key] = value;
    }
  }

  return result;
}

export function buildUrl(operation: Operation, values: PlainRecord): string {
  let path = operation.path;

  for (const [key, rawValue] of Object.entries(values)) {
    path = path.replace(`{${key}}`, encodeURIComponent(String(rawValue)));
  }

  const query = new URLSearchParams();
  const pathFieldNames = new Set(
    [...operation.path.matchAll(/\{([^}]+)\}/g)].map((match) => match[1])
  );

  for (const field of operation.fields) {
    if (pathFieldNames.has(field.name)) {
      continue;
    }

    const value = values[field.name];
    const isQueryField =
      operation.method === "GET" ||
      operation.id === "addCopies" ||
      field.name === "status" ||
      field.name === "unpaid_only";

    if (!isQueryField || value === "" || value === undefined || value === null) {
      continue;
    }

    query.set(field.name, String(value));
  }

  const queryString = query.toString();
  return `${getApiBaseUrl()}${path}${queryString ? `?${queryString}` : ""}`;
}

export async function callOperation(
  operation: Operation,
  formValues: PlainRecord
): Promise<PlainRecord | { ok: true; status: number }> {
  if (operation.disabledReason) {
    throw new Error(operation.disabledReason);
  }

  const values = normalizeFormValues(formValues);
  const url = buildUrl(operation, values);
  const headers: HeadersInit = { Accept: PROTO_CONTENT_TYPE };
  let body: Uint8Array | undefined;

  if (operation.requestType) {
    headers["Content-Type"] = PROTO_CONTENT_TYPE;
    body = await encodeMessage(operation.requestType, buildRequestBody(operation, values));
  }

  let requestBody: BodyInit | undefined;
  if (body) {
    const copy = new Uint8Array(body.byteLength);
    copy.set(body);
    requestBody = copy.buffer as ArrayBuffer;
  }

  const response = await fetch(url, {
    method: operation.method,
    headers,
    body: requestBody
  });

  if (!response.ok) {
    throw new Error(await decodeErrorResponse(response));
  }

  if (!operation.responseType || response.status === 204) {
    return { ok: true, status: response.status };
  }

  return decodeMessage(operation.responseType, await response.arrayBuffer());
}
