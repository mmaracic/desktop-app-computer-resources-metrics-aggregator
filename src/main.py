"""Desktop application entry point combining FastAPI, uvicorn, and pywebview."""

import argparse
import asyncio
import logging
import threading
from threading import Semaphore

import uvicorn
import webview
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.concurrency import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.api import api
from src.colored_log_formatter import ColoredLogFormatter
from src.config.environment_config import EnvironmentConfig
from src.dev_proxy import _dev_proxy
from src.metric.metric_registry import MetricRegistry
from src.observers.aggregation_observer import AggregationObserver
from src.providers.ati_gpu_provider import AtiGpuProvider
from src.providers.resource_utilization_provider import ResourceUtilizationProvider
from src.providers.temperature_provider import TemperatureProvider
from src.updaters.file_updater import FileUpdater
from src.updaters.react_ui_updater import ReactUiUpdater

log_handler = logging.StreamHandler()
log_handler.setFormatter(
    ColoredLogFormatter(
        fmt="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)
logging.basicConfig(level=logging.INFO, handlers=[log_handler])
logger = logging.getLogger(__name__)


class Config(BaseModel):
    """Configuration for the application."""

    host: str = "127.0.0.1"
    port: int = 5000
    dev: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI application.
    """
    logger.info("Starting FastAPI application...")
    env_config = EnvironmentConfig()
    app.state.env_config = env_config

    file_updater = FileUpdater(env_config.metric_filename)
    react_ui_updater = ReactUiUpdater()
    app.state.react_ui_updater = react_ui_updater

    metric_registry = MetricRegistry()
    metric_registry.register_metric_provider(AtiGpuProvider())
    metric_registry.register_metric_provider(ResourceUtilizationProvider())
    metric_registry.register_metric_provider(TemperatureProvider())

    metric_registry.register_metric_observer(
        AggregationObserver([file_updater, react_ui_updater])
    )
    app.state.metric_registry = metric_registry

    stop_event = threading.Event()
    metric_thread = threading.Thread(
        target=lambda: asyncio.run(
            fetch_metrics_periodically(metric_registry, env_config, stop_event)
        ),
        daemon=True,
    )
    metric_thread.start()
    yield
    logger.info("Shutting down FastAPI application...")
    stop_event.set()
    metric_thread.join(timeout=10)
    metric_registry.unregister_all_providers_observers()
    logger.info("FastAPI application shutdown complete")


async def fetch_metrics_periodically(
    metric_registry: MetricRegistry,
    env_config: EnvironmentConfig,
    stop_event: threading.Event,
):
    """Background task that fetches metrics at regular intervals, running in its own thread."""
    logger.info("Starting background metric fetching task")
    while not stop_event.is_set():
        metric_registry.extract_metrics()
        await asyncio.sleep(env_config.metric_refresh_interval)


app = FastAPI(lifespan=lifespan)
app.include_router(api.router, prefix="/api")


@app.websocket("/websocket")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for real-time metric streaming.

    The server sends metrics periodically from background tasks without waiting
    for client messages. Background tasks automatically stop when the connection
    closes or server shuts down.
    """
    await websocket.accept()
    try:
        # Just keep the connection alive, background task handles sending
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")


async def _run_backend_server(
    config: Config, sem: Semaphore, server_holder: list[uvicorn.Server]
) -> None:
    """Start the uvicorn server in a background thread with a semaphore to block main thread until the server is ready."""
    uvicorn_config = uvicorn.Config(
        app, host=config.host, port=config.port, log_level="info", log_config=None
    )
    server = uvicorn.Server(uvicorn_config)
    server_holder.append(server)  # Store the server instance in the list
    logger.info("Starting backend server at http://%s:%d", config.host, config.port)
    server_task = asyncio.create_task(server.serve())

    # Wait until Uvicorn explicitly flags that it's ready
    while not server.started:
        await asyncio.sleep(0.1)

    logger.info(
        "Backend server is ready and running at http://%s:%d",
        config.host,
        config.port,
    )
    sem.release()  # Release the semaphore to unblock the main thread

    await server_task


def parse_args() -> Config:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Agentic desktop application")
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="Host for the backend server"
    )
    parser.add_argument(
        "--port", type=int, default=5000, help="Port for the backend server"
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run in development mode, pointing the webview at the Vite dev server",
    )
    args = parser.parse_args()
    return Config(host=args.host, port=args.port, dev=args.dev)


def main() -> None:
    """Main entry point for the application."""
    config = parse_args()

    if not config.dev:
        app.mount("/", StaticFiles(directory="react/dist", html=True))
    else:
        app.add_api_route("/", _dev_proxy, methods=["GET", "HEAD", "OPTIONS"])
        app.add_api_route(
            "/{path:path}", _dev_proxy, methods=["GET", "HEAD", "OPTIONS"]
        )

    server_holder: list[uvicorn.Server] = []  # List to hold the server instance
    sem = Semaphore(0)  # Semaphore to block main thread until the server is ready
    # Python application shuts down when only daemon threads are running.
    # Running the backend server in a daemon thread rather than in webview start method
    # allows the application to exit gracefully when the webview window is closed.
    thread = threading.Thread(
        target=lambda: asyncio.run(_run_backend_server(config, sem, server_holder)),
        daemon=True,
    )
    thread.start()
    sem.acquire()  # Block main thread until the server is ready

    server_url = f"http://{config.host}:{config.port}"
    logger.info("Connecting to backend server at %s", server_url)
    window = webview.create_window("Hello world", server_url)
    if window is None:
        logger.error("Failed to create webview window, shutting down backend server...")
        return
    window.events.shown += lambda: logger.info("Webview window is now visible")
    webview.start()

    logger.info("Webview window closed, shutting down backend server...")
    # Signal uvicorn to exit gracefully so the FastAPI lifespan shutdown runs.
    backend_server = server_holder[0]
    backend_server.should_exit = True
    thread.join(timeout=10)


if __name__ == "__main__":
    main()
