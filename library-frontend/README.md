# Library Frontend

Next.js frontend for the Library backend REST API.

The UI accepts clear text values in forms and displays decoded clear text output. API traffic uses protobuf where the backend protobuf schema supports it:

- Request header: `Content-Type: application/x-protobuf`
- Response header: `Accept: application/x-protobuf`
- Schema: `public/proto/library.proto`

## Dependencies

- Node.js 20 or newer
- npm 10 or newer
- Running backend API at `http://localhost:8000`

Runtime packages:

- `next`
- `react`
- `react-dom`
- `protobufjs`
- `lucide-react`

Test packages:

- `vitest`
- `jsdom`
- `@testing-library/react`
- `@testing-library/jest-dom`
- `@vitejs/plugin-react`

## Configure

From the frontend directory:

```bash
cd /Volumes/SSK/InterView_Knowledge/Library1/library_frontend
cp .env.example .env.local
```

Default `.env.local`:

```bash
NEXT_PUBLIC_LIBRARY_API_BASE_URL=http://localhost:8000/api/v1
```

## Install

```bash
npm install
```

## Run Backend

In another terminal, start the backend from the backend directory:

```bash
cd /Volumes/SSK/InterView_Knowledge/Library1/library-backend
source .venv/bin/activate
export DATABASE_URL=postgresql+asyncpg://library_user:library_pass@localhost:5432/library_db
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open backend docs:

```text
http://localhost:8000/docs
```

## Run Frontend

```bash
cd /Volumes/SSK/InterView_Knowledge/Library1/library_frontend
npm run dev
```

Open:

```text
http://localhost:3000
```

## Compile Production Build

```bash
npm run build
npm run start
```

Production start defaults to:

```text
http://localhost:3000
```

## Automated Tests

```bash
npm test
```

The tests validate:

- protobuf encoding and decoding
- URL/query construction from clear text form values
- protobuf request headers and binary request body
- borrow date conversion into `google.protobuf.Timestamp`

## API Coverage

The UI exposes:

- Authors: list, get, create, update, delete
- Books: list, get, create, update, delete
- Book copies: list, add copies
- Members: list, get, create, update, delete
- Loans: list, get, borrow, return, borrowed books, due books, mark overdue
- Fines: transaction fines, member fines, pay fines
- Stats: library stats

One backend schema gap is shown in the UI: `PATCH /books/copies/{copy_id}/status` requires a body, but `library.proto` does not currently define a protobuf request message for that body. Add a protobuf request message and backend serializer mapping to make that endpoint protobuf-only like the others.
