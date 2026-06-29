# ZimFire Monitor — Deployment

Headless worker that polls **EUMETSAT MTG** and **NASA FIRMS VIIRS**, classifies
fire risk against your areas of interest (`src/aoi.geojson`), and writes GeoJSON +
a ranked CSV to a persistent `output` volume every `POLL_INTERVAL_SECONDS`.

```
.
├── Dockerfile
├── docker-compose.yml      # the Portainer stack
├── requirements.txt        # pinned, worker-only deps
├── healthcheck.py          # container healthcheck
├── .env.example            # copy to .env and fill in
├── .dockerignore
├── config.py  main.py
└── src/aoi.geojson         # your monitored compartments (baked into image)
```

## 1. Configuration

The compose file does **not** use `env_file` (that path doesn't exist when
Portainer deploys a stack). Instead every variable is interpolated, fed from:

- **Portainer** → the stack's *Environment variables* panel, or
- **CLI** → a local `.env` file, which `docker compose` loads automatically.

For the CLI workflow:

```bash
cp .env.example .env
# edit .env and paste your EUMETSAT + FIRMS credentials
```

Only `EUMETSAT_CONSUMER_KEY`, `EUMETSAT_CONSUMER_SECRET`, and `FIRMS_MAP_KEY`
are required to start. The rest have working defaults; Telerivet keys are
optional (see note at the bottom).

> **Security:** the `_env` file you originally had contains live keys. Treat them
> as leaked and rotate the EUMETSAT secret, FIRMS map key, and Telerivet key
> before using them again. Never commit `.env`.

## 2a. Deploy via Portainer (recommended)

Build the image **once on the Docker host**, then deploy a stack that just
references it. This way Portainer never needs a build context (the cause of the
`"/src/aoi.geojson": not found` error — Portainer's stack build context didn't
include the `src/` folder).

**Step 1 — build the image on the host** (from inside this folder, so the full
directory is the build context):

```bash
cd ZimFire-Deploy
docker build -t zimfire-monitor:latest .
```

**Step 2 — deploy the stack in Portainer:**

1. Portainer → **Stacks** → **Add stack**.
2. Name it (e.g. `zimfire`). The **Web editor** is fine now — paste the contents
   of `docker-compose.yml` (it has no `build:` step, so no files are needed).
3. Under **Environment variables**, add at least the three required keys:
   `EUMETSAT_CONSUMER_KEY`, `EUMETSAT_CONSUMER_SECRET`, `FIRMS_MAP_KEY`
   (add `POLL_INTERVAL_SECONDS`, `RUN_ONCE`, etc. only to override defaults).
4. **Deploy the stack.**

Watch the container's **Logs**; you'll see `Starting fire monitoring cycle ...`
and `Exported .../ranked_fire_alerts.csv`.

When you change code or the AOI, rebuild (`docker build -t zimfire-monitor:latest .`)
and redeploy/recreate the stack to pick up the new image.

## 2b. Deploy from the Docker host CLI (simplest to test)

Use the build-enabled compose file, which builds and runs in one command and
reads your local `.env`:

```bash
cp .env.example .env   # fill in credentials first
docker compose -f docker-compose.build.yml up -d --build
docker compose -f docker-compose.build.yml logs -f
```

## 3. Test a single cycle

Set `RUN_ONCE=true` in `.env` (or as an env override) to run one cycle and exit —
handy for confirming credentials and AOI before leaving it on the 15-minute loop.

```bash
RUN_ONCE=true docker compose -f docker-compose.build.yml run --rm fire-monitor
```

## 4. Where the data lives

Two named volumes persist across restarts and image rebuilds:

| Volume        | Mount               | Contents                                  |
| ------------- | ------------------- | ----------------------------------------- |
| `fire_output` | `/app/output`       | `*.geojson`, `ranked_fire_alerts.csv`     |
| `fire_db`     | `/app/src/db`       | `alerts.db` (sqlite dedup store)          |

Copy outputs to the host whenever you need them:

```bash
docker cp zimfire-monitor:/app/output ./output
```

## 5. Updating

After changing code, rebuild and recreate — volumes (and your data) survive:

```bash
docker compose up -d --build
```

To change which areas are monitored, replace `src/aoi.geojson` and rebuild
(the AOI is baked into the image, not a volume).

---

### Notes / things to know

- **No SMS in this build.** `config.py` reads the Telerivet variables but
  `main.py` never sends anything — the loop only produces GeoJSON/CSV. Wiring
  Telerivet into `run_once()` is a small follow-up if you want alerts dispatched.
- **Dependencies were trimmed.** `streamlit`, `folium`, `streamlit-folium`,
  `branca`, `matplotlib`, and `openpyxl` from the original `requirements.txt`
  are not imported by `main.py`, so they're excluded to keep the image small.
  If you have a separate Streamlit dashboard, it should be its own service/image.
- **Directory casing was fixed.** The original archive shipped `SRC/` and
  `Output/` (capitalised), but `config.py` looks for lowercase `src/` and
  `output/`. That works on Windows/macOS but fails on Linux containers, so the
  AOI now lives at `src/aoi.geojson`.
- **Healthcheck** marks the container healthy once `ranked_fire_alerts.csv` is
  written and refreshed within ~3 poll intervals. Remove the `HEALTHCHECK` line
  from the Dockerfile if you'd rather not have it.
