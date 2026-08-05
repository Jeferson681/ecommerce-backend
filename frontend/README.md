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

## Implemented modules

The frontend mirrors the backend domains and implements the following modules:

- `auth` — login, signup, logout, session storage
- `user` — profile management
- `product` — product listing, search, and detail
- `cart` — shopping cart operations (client state + API)
- `order` — orders and checkout
- `payment` — Stripe payment integration
- `account` — account overview and order history
- `storefront` — landing page and product discovery

Routes are defined under `app/` and delegate to module pages.
