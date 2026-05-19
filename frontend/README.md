# frontend

Next.js (App Router) frontend organized by backend-like bounded contexts.

## Run

Prereqs:
- Backend API running at `http://localhost:8000`

Commands:

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Architecture

- `core/`: cross-cutting concerns (API config, fetch wrapper, error types, utilities)
- `shared/`: design-system-ish UI primitives and app shell layout
- `modules/`: feature modules (bounded contexts)
	- Each module contains:
		- `types/`: TS types matching API payloads
		- `services/`: API calls (no UI)
		- `hooks/`: client state/data fetching hooks
		- `components/`: presentational components
		- `pages/`: page-level composition used by Next routes
- `app/`: Next.js route definitions only (thin wrappers around module pages)

API base URL is fixed in [core/config/api.ts](core/config/api.ts).

## Implemented module

Only the `user` module is implemented right now.

Routes:
- `/` redirects to `/users`
- `/users` list + delete
- `/users/new` create
- `/users/[id]` details
- `/users/[id]/edit` edit (uses `PUT /users/:id`)
