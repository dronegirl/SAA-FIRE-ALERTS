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

## 1. One-time setup

```bash
cp .env.example .env
# edit .env and paste your EUMETSAT + FIRMS credentials
```

Only `EUMETSAT_CONSUMER_KEY`, `EUMETSAT_CONSUMER_SECRET`, and `FIRMS_MAP_KEY`
are required to start. Telerivet keys are optional (see note at the bottom).

> **Security:** the `_env` file you originally had contains live keys. Treat them
> as leaked and rotate the EUMETSAT secret, FIRMS map key, and Telerivet key
> before using them again. Never commit `.env`.

## 2a. Deploy via Portainer (recommended)

Portainer needs the build context, so use a method that uploads the whole folder:

1. Put this folder on your Docker host (e.g. `git push` to a repo, or copy it over).
2. Portainer → **Stacks** → **Add stack**.
3. Choose **Repository** (point at your git repo) **or** **Upload** (upload this
   folder as a tarball/zip). The plain *Web editor* cannot build from local files.
4. Set the stack name (e.g. `zimfire`).
5. Under **Environment variables**, either upload your `.env` or paste the same
   key/value pairs the stack expects.
6. **Deploy the stack.**

Portainer builds `zimfire-monitor:latest` and starts the `fire-monitor` service.
Watch progress under the container's **Logs**; you'll see `Starting fire
monitoring cycle ...` and `Exported .../ranked_fire_alerts.csv`.

## 2b. Deploy from the Docker host CLI (simplest to test)

```bash
docker compose up -d --build
docker compose logs -f
```

## 3. Test a single cycle

Set `RUN_ONCE=true` in `.env` (or as an env override) to run one cycle and exit —
handy for confirming credentials and AOI before leaving it on the 15-minute loop.

```bash
RUN_ONCE=true docker compose run --rm fire-monitor
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
