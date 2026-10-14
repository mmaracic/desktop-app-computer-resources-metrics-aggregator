# Readme

Python desktop application that periodically samples computer resource metrics (CPU, memory, disk, network, AMD GPU, temperature sensors, top processes), stores the changes as daily files, and shows them in a React Typescript UI using PyWebView.  
https://pywebview.flowrl.com/

The frontend is documented in [react/README.md](react/README.md).

## Setup
Run the following command to install the backend dependencies:
```bash
uv sync
```

Run the following command to install the frontend dependencies:
```bash
cd react
npm install
```

## Run
Build the frontend with:
```bash
cd react
npm run build
```

Run the application from the repository root (the build is served from `react/dist`, relative to the working directory):
```bash
uv run -m src.main
```
The application accepts the following parameters:
- `--host` - backend server host (default `127.0.0.1`)
- `--port` - backend server port (default: random port in 49152-65535)
- `--dev` - development mode, see below
- `--log-to-file` - also log to a rotating `application_<timestamp>.log` file (10 MB, 5 backups) in the project root
- `--fe-debug` - enable the webview inspector (right-click -> Inspect Element)

## Configuration
Settings are read from environment variables or a `.env` file (names are case-insensitive):

| Variable | Default | Description |
| --- | --- | --- |
| `METRIC_REFRESH_INTERVAL` | `5` | Seconds to wait between metric collections (CPU sampling adds about 1 s) |
| `METRIC_FILENAME` | `daily_metrics` | Base name of the daily metric files (`daily_metrics_YYYYMMDD.json`) |
| `AZURE_USAGE_ENABLED` | `false` | Enable the Azure Blob Storage upload and tiering done at startup |
| `AZURE_BLOB_CONTAINER_NAME` | `metrics` | Azure Blob container name |
| `AZURE_BLOB_CONNECTION_STRING` | none | Azure Blob Storage connection string; required even when Azure is disabled, otherwise the app fails to start |

Metric definitions live in `metadata/metric_metadata.json` and `metadata/temperature_metadata.json` (the latter is overridden by the former on name clashes). UI metric settings (enabled, color, order) are saved to `metric_config.json` in the project root.

## Backend overview
- `src/main.py` - FastAPI app, lifespan setup, background collection thread, uvicorn thread and PyWebView window. In non-dev mode `react/dist` is mounted at `/`.
- `src/providers` - metric providers (all names must exist in the metadata files, otherwise collection fails):
  - `ResourceUtilizationProvider` (psutil) - CPU usage/frequency/count, memory, swap, disk usage and I/O, network bytes; I/O and network values are cumulative counters. Uses Linux-only memory fields.
  - `AtiGpuProvider` - AMD GPUs read from Linux sysfs (`/sys/class/drm`, vendor `0x1002`): busy, VRAM, GTT, temperature, clocks, power, fan. Metadata exists for `card0` and `card1` only.
  - `TemperatureProvider` (psutil sensors, Linux/FreeBSD) - temperature and fan sensors; the `amdgpu` chip is skipped.
  - `TopProcessesProvider` - `top_process_1..5` ranked by CPU share times memory share, as dict values.
- `src/metric` - registry, provider/observer interfaces and metric models
- `src/observers` - `AggregationObserver` drops `None` values and forwards only metrics that changed by at least their `minimal_delta` (dicts when they differ)
- `src/updaters` - `FileUpdater` appends to the daily file; `ReactUiUpdater` is currently a no-op
- `src/storage` and `src/service` - local disk and Azure Blob storage, retrieval by datetime range
- `src/samplers` - `UniformMetricSampler` splits the range into `bucket_count` buckets and keeps the maximum per metric in each (the most common value for dict metrics), timestamped at the bucket's median
- `src/api` - REST routes under `/api`

### Data files
Each day has one file, `daily_metrics_YYYYMMDD.json` (UTC date), in the working directory. Despite the extension they are JSON Lines: one `{"stored_at": ..., "metrics": [{"name", "value"}]}` object per line, containing only the metrics that changed since the last write.

### API
- `GET /api/metrics/range` - metrics between `start_datetime` and `end_datetime` (ISO 8601 with a UTC offset), sampled to `bucket_count` (default 100); optional `container_name` also reads missing files from Azure. Returns 400 for invalid or reversed dates.
- `GET /api/metrics/metadata` - list of metric metadata, each with the raw metric `name`; limited to metrics found in the last 2 days of local data, or all metrics if none are found
- `GET /api/metrics/config` - saved metric configurations (`[]` if none)
- `POST /api/metrics/config` - overwrite the saved metric configurations
- `WS /websocket` - accepts connections but does not currently send data; the UI polls the REST endpoints

Local files take precedence over Azure files when retrieving a range.

### Azure Blob Storage
When `AZURE_USAGE_ENABLED=true`, only at startup the app uploads local daily files that are not yet in the container (skipping today's file), then moves Hot blobs older than 7 days to Cold. The tier step covers every blob in the container and raises if one is in a tier other than Hot or Cold.

### Running the application on Ubuntu

In Ubuntu additional dependencies are required to run the application. Install them with:  

Requested by PyCairo, which is a dependency of PyWebView.
```bash
sudo apt install cmake
sudo apt install libcairo2-dev pkg-config python3-dev

```
Requested by PyGObject, which is a dependency of PyWebView.
```bash
sudo apt install libgirepository1.0-dev 
```
Two environment variables are preventing successfull startup of PYWebView on Ubuntu. Use to remove them before running the application:
```bash
unset GTK_PATH
unset GIO_MODULE_DIR
```
https://stackoverflow.com/questions/75921414/java-symbol-lookup-error-snap-core20-current-lib-x86-64-linux-gnu-libpthread

## Development mode
In development mode the application proxies frontend requests to the Vite dev server, so no build step is needed. Start both servers in separate terminals:
```bash
# Terminal 1 — Vite dev server with hot module replacement
cd react && npm run dev

# Terminal 2 — FastAPI backend with dev proxy (port must match the Vite proxy target)
uv run -m src.main --dev --port 5000
```
The webview opens the backend URL (`http://127.0.0.1:5000`). FastAPI forwards non-API GET/HEAD/OPTIONS requests to Vite at `http://localhost:5173` (hard-coded), while Vite proxies `/api` back to `127.0.0.1:5000`, so changes to React source files are reflected immediately without rebuilding.

## Features
- FastAPI backend server with API routes prefixed under `/api`
- React frontend served from the FastAPI backend as static files using `StaticFiles` middleware and mounting the React build directory
- React Typescript frontend built with Vite
- PyWebView creates a frontend window and serves the React app from the FastAPI backend
- Backend server runs in a background thread, allowing the application to exit gracefully when the webview window is closed
- Logging for backend server startup and webview window events with colored log levels
- Dev mode (`--dev`) proxies frontend requests to the Vite dev server, removing the need to build the frontend during development
- Command-line arguments for configuring host, port, dev mode, file logging and the webview inspector
- Periodic metric collection written to daily JSON Lines files, with optional Azure Blob Storage archiving at startup
- Time-range queries sampled into buckets
- Graph UI with per-component/unit tabs, configurable metrics, and dark/light theme

## Tests
```bash
uv run -m pytest
```

# Issues
- The GPU and temperature providers are Linux-only, and `ResourceUtilizationProvider` uses Linux-only memory fields.
- A sensor chip/label, fan or third AMD GPU without a metadata entry raises an error that stops the background collection loop.
- `/websocket` does not stream data.

# To Do
- Add support for non-Linux platforms for GPU and temperature providers.
- Stream logs in real-time from the backend to the frontend.
- Improve error handling for missing sensor metadata.
- Implement streaming for `/websocket` endpoint.
- Add UI to configure and manage application settings
- Add UI to add, remove or edit metric metadata