# Readme

Python desktop application with React Typescript UI using PyWebView.  
https://pywebview.flowrl.com/

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
cd frontend
npm run build
```

Run the application with:
```bash
uv run -m src.main
```
The application accepts `--host` and `--port` parameters to configure the backend server address.

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

# Terminal 2 — FastAPI backend with dev proxy
uv run -m src.main --dev
```
The webview opens `http://127.0.0.1:5000`. FastAPI forwards all non-API requests to Vite at `http://localhost:5173`, so changes to React source files are reflected immediately without rebuilding.

## Features
- FastAPI backend server with API routes prefixed under `/api`
- React frontend served from the FastAPI backend as static files using `StaticFiles` middleware and mounting the React build directory
- React Typescript frontend built with Vite
- PyWebView creates a frontend window and serves the React app from the FastAPI backend
- Backend server runs in a background thread, allowing the application to exit gracefully when the webview window is closed
- Logging for backend server startup and webview window events with colored log levels
- Dev mode (`--dev`) proxies frontend requests to the Vite dev server, removing the need to build the frontend during development
- Command-line arguments for configuring host and port

# Issues
- None currently known.