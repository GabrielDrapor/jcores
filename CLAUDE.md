# JCores

A podcast discovery app for [Gcores](https://gcores.com), deployed at https://g.jrd.pub

## Architecture

- **Frontend**: Next.js 15 (React 19, Tailwind CSS) — `app/`
- **Backend**: FastAPI (Python) — `api/`
- **Database**: Cloudflare D1 (SQLite) via HTTP API
- **Cache**: Cloudflare KV
- **Deployment**: Vercel (Next.js + Python serverless functions)
- **Image proxy**: `/api/py/image-proxy/` proxies `image.gcores.com` to avoid CORS

## Development

```bash
# Frontend only
npm run next-dev

# Backend only (requires .env.local with Cloudflare credentials)
npm run fastapi-dev

# Both concurrently
npm run dev
```

Python venv lives at `api/.venv`. Activate with `source api/.venv/bin/activate`.

## Environment Variables

All set via Vercel; pull with `vercel env pull .env.local`:
- `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_EMAIL`, `CLOUDFLARE_API_KEY` — Cloudflare auth
- `CLOUDFLARE_NAMESPACE_ID` — KV cache namespace
- `D1_DATABASE_ID` — D1 database UUID

## Key Files

- `app/page.js` — entry point, fetches initial data
- `app/components/episodes-client.js` — main UI with filters and infinite scroll
- `api/main.py` — FastAPI routes
- `api/db.py` — D1 query helpers, Cloudflare KV cache
- `api/crud.py` — data access functions (raw SQL against D1)
- `api/models.py` — reserved user/album ID constants
- `api/schemas.py` — Pydantic response models
- `scripts/backfill.py` — data crawler/ingestion (legacy, uses SQLAlchemy)
- `scripts/migrate_to_d1.py` — one-time PostgreSQL → D1 migration
