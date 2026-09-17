"""Desktop application entry point combining FastAPI, uvicorn, and pywebview."""

import argparse
import asyncio
import logging
import logging.handlers
import threading
from datetime import datetime
from pathlib import Path
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
from src.storage.azure_blob_storage import AzureBlobStorage
from src.storage.disk_text_file_storage import DiskTextFileStorage
from src.storage.storage_service import StorageService
from src.updaters.file_updater import FileUpdater
from src.updaters.react_ui_updater import ReactUiUpdater


def setup_logging(
    log_to_file: bool = False, log_level: int = logging.INFO
) -> logging.Logger:
    """Configure logging based on the log_to_file and log_level parameters.

    Called twice: once for the console handler and once for the file handler in the main application if enabled.

    Args:
        log_to_file: If True, logs will be written to a file in addition to console.
                    If False, logs will only go to console.
        log_level: The minimum level of messages that will be logged.

    Returns:
        The root logger instance.
    """
    # Create formatter
    formatter = ColoredLogFormatter(
        fmt="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # File handler (only if log_to_file is True)
    file_handler = None
    if log_to_file:
        # Get the directory of this script for log file location
        script_dir = Path(__file__).parent.parent.resolve()
        
        # Create timestamped log file name (YYYY-MM-DD_HH-MM-SS format)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = script_dir / f"application_{timestamp}.log"
        
        # Create rotating file handler to prevent unbounded growth
        max_bytes = 10 * 1024 * 1024  # 10 MB
        backup_count = 5
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Add handlers
    root_logger.addHandler(console_handler)
    if file_handler:
        root_logger.addHandler(file_handler)

    logger = logging.getLogger(__name__)
    return logger


# Setup logging at module level (can be reconfigured per run)
logger = setup_logging(
    log_to_file=False, log_level=logging.INFO
)  # Default to console only


class Config(BaseModel):
    """Configuration for the application."""

    host: str = "127.0.0.1"
    port: int = 5000
    dev: bool = False
    log_to_file: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI application.
    """
    logger.info("Starting FastAPI application...")
    env_config = EnvironmentConfig()
    app.state.env_config = env_config

    disk_storage = DiskTextFileStorage(base_path=".")
    file_updater = FileUpdater(env_config.metric_filename, disk_storage)
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

    if env_config.azure_usage_enabled:
        azure_storage = AzureBlobStorage(
            connection_string=env_config.azure_blob_connection_string
        )
        storage_service = StorageService(
            azure_storage=azure_storage,
            disk_storage=disk_storage,
            base_file_name=env_config.metric_filename,
        )
        storage_service.upload_local_files_to_azure(
            env_config.azure_blob_container_name
        )
        storage_service.change_tier_of_blobs_in_azure(
            env_config.azure_blob_container_name
        )

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
    parser.add_argument(
        "--log-to-file",
        action="store_true",
        help="Enable logging to application.log file (in addition to console)",
    )
    args = parser.parse_args()
    return Config(
        host=args.host, port=args.port, dev=args.dev, log_to_file=args.log_to_file
    )


def main() -> None:
    """Main entry point for the application."""
    config = parse_args()

    # Setup logging based on configuration
    logger = setup_logging(log_to_file=config.log_to_file)

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
