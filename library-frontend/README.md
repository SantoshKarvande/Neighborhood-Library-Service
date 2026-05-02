# 📚 Neighborhood Library Service — Frontend

**Next.js 14 (TypeScript)** frontend for the Neighborhood Library Service. Communicates with the FastAPI backend over both **JSON** and **Protocol Buffers (Protobuf)** using the App Router architecture.

---

## 🧰 Tech Stack

| Technology | Purpose |
|---|---|
| Next.js 14 | React framework (App Router) |
| TypeScript | Type safety |
| protobufjs | Runtime Protobuf encode/decode |
| lucide-react | Icon library |
| Vitest | Unit testing |
| Docker | Containerisation |

---

## 🗂️ Project Structure

```
library-frontend/
├── app/
│   ├── globals.css              ← Global styles
│   ├── layout.tsx               ← Root layout component
│   └── page.tsx                 ← Home page
├── lib/
│   ├── api.ts                   ← API fetch wrappers (JSON + Protobuf)
│   └── protobuf.ts              ← Protobuf encode/decode helpers
├── public/
│   └── proto/
│       ├── library.proto        ← Protobuf schema (loaded at runtime)
│       └── google/protobuf/
│           └── timestamp.proto  ← Google well-known type
├── tests/
│   ├── protobuf-client.test.ts  ← Vitest tests for Protobuf client
│   └── setup.ts                 ← Vitest setup
├── Dockerfile                   ← Multi-stage production image
├── .dockerignore
├── .env.example
├── .eslintrc.json
├── next.config.mjs
├── package.json
├── tsconfig.json
└── vitest.config.ts
```

---

## ✅ Prerequisites (Local Development)

| Tool | Version |
|---|---|
| Node.js | 18+ |
| npm | 9+ |
| Docker Desktop | Latest (for Docker workflow) |

> To run via Docker only, Docker Desktop is the sole requirement.

---

## 🐳 Run with Docker (Recommended)

Use the **root-level** `docker-compose.yml` to start the full stack (DB + backend + frontend) together:

```bash
# From the project root — Neighborhood-Library-Service/
docker-compose up --build
```

Frontend will be available at: **http://localhost:3000**

> The frontend container depends on the backend being healthy before it starts. Docker Compose handles this automatically.

---

## 🛠️ Local Development Setup

### 1. Install dependencies

```bash
cd library-frontend
npm install
```

> This also generates `package-lock.json` if it doesn't exist. Commit this file to git.

### 2. Configure environment variables

```bash
cp .env.example .env.local
```

Update `.env.local`:

```env
# Point to the running backend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> When running inside Docker Compose, the frontend container uses `http://backend:8000` internally. For local development outside Docker, use `http://localhost:8000`.

### 3. Start the development server

```bash
npm run dev
```

Frontend available at: **http://localhost:3000**

---

## 🏗️ Build for Production

```bash
# Create optimised production build
npm run build

# Serve the production build
npm run start
```

---

## 🔄 Protocol Buffers

The frontend loads the Protobuf schema at **runtime** from `public/proto/library.proto` using `protobufjs`. No compile step is needed on the frontend.

The helper functions are in `lib/protobuf.ts`:
- Encode a JS object → Protobuf binary before sending to the API
- Decode Protobuf binary → JS object when receiving from the API

> Keep `public/proto/library.proto` in sync with `library-backend/proto/library.proto`.

---

## 🔌 API Communication

`lib/api.ts` provides fetch wrappers that support both encodings:

**JSON (default):**
```typescript
// No special headers required
const response = await fetch(`${API_URL}/api/v1/books`);
```

**Protobuf:**
```typescript
// Set both headers to use Protobuf
fetch(`${API_URL}/api/v1/books`, {
  headers: {
    'Content-Type': 'application/x-protobuf',
    'Accept':       'application/x-protobuf',
  }
});
```

---

## 🧪 Running Tests

```bash
# Run all tests once
npm run test

# Run in watch mode
npm run test:watch
```

Tests are located in the `tests/` directory and configured via `vitest.config.ts`.

---

## 🔧 Available Scripts

| Script | Command | Description |
|---|---|---|
| Dev server | `npm run dev` | Start with hot reload at http://localhost:3000 |
| Production build | `npm run build` | Optimised build in `.next/` |
| Production server | `npm run start` | Serve the production build |
| Lint | `npm run lint` | Run ESLint |
| Test | `npm run test` | Run Vitest once |
| Test watch | `npm run test:watch` | Run Vitest in watch mode |

---

## 🌍 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000` |

> `NEXT_PUBLIC_` prefix makes the variable available in the browser bundle. It is baked in at **build time**, so the correct URL must be set before running `npm run build` or `docker-compose up --build`.

---

## 🐳 Docker Reference

The frontend Dockerfile uses a **multi-stage build**:
- `deps` — installs `node_modules`
- `builder` — runs `npm run build`
- `runtime` — minimal final image with only the built output

```bash
# Build image standalone
docker build -t library-frontend ./library-frontend

# Run standalone (backend must be reachable)
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000 \
  library-frontend
```
