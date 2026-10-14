# Computer Resources Metrics - React UI

This is the React frontend for the Computer Resources Metrics Aggregator application. It provides an interactive dashboard for visualizing computer resource metrics using D3.js graphs with a modern shadcn/ui design system built on Tailwind CSS.

## Features

### Tabs and Theme
- **Graph / Configuration tabs**: Switch between the graph view and metric configuration
- **Theme selector**: System, Light or Dark; persisted in `localStorage` and applied via the `dark` class on `<html>`

### Time Range Picker
- **Date & Time Inputs**: Select custom start and end dates/times for metrics data
- **Show Present Checkbox**: Checked by default; the end date/time is locked and the range is relative to now
- **Preset Duration**: While "Show Present" is checked, choose Last 1h / 3h (default) / 6h / 12h / 24h / 7 days
- **Extra Controls**: Graph tab type (Component type or Metric unit), Graph selector (Radio or Checkbox), and Buckets (100, 250, 500, 1000)
- **Reset Button**: Restores the 3-hour present range, Show Present, and the default Graph tab type, Graph selector and Buckets
- **Timezone-Aware**: Timestamps are sent with the local timezone offset
- Auto-refreshes graph data whenever the time range or bucket count changes

### Metrics Graph
- **D3.js Visualization**: Interactive line graphs with smooth curves showing metric trends over time
- **Grouped Tabs**: Enabled metrics are split into tabs by component type (e.g. CPU, GPU 0, GPU 1) or by metric unit
- **Clickable Data Points**: Click a point to see all metric values at that timestamp
- **Hover Tooltips**: Hovering a line shows its name; hovering a point shows its value and enlarges it
- **Line Labels**: Each line is labelled above its highest point
- **Series Selector**: In Radio mode, pick one line (or All) to fit the Y axis to it and dim the others; in Checkbox mode, toggle lines on/off
- **Drag to Zoom**: Drag across the plot to select a time range; it is applied to the time range picker
- **Smooth Curves**: Monotone X curve interpolation
- **Dynamic Scales**: Y axis fits the visible data with 10% padding
- **Unit Conversion**: Bytes are shown as MB and milliwatts as W
- **Responsive Layout**: Graph resizes with the window

### Configuration Section
- **Enable/Disable Metrics**: Toggle visibility of individual metrics with checkboxes
- **Default to Enabled**: When no configuration exists, every available metric defaults to enabled
- **Flip All Enabled**: Invert the enabled state of every metric
- **Filtering**: Filter by name/alias and by component type
- **Sorting**: Sort by saved order, or by type then name
- **Color Selection**: Pick from a 21-color preset palette or a custom RGB color
- **Reordering**: Move metrics up/down using arrow buttons
- **Remove Metrics**: Delete a config entry (disabled while showing the default, unsaved configuration)
- **Save Configuration**: Persist changes through `POST /api/metrics/config`

### Popup Details
- **Exact Values**: Shows values (2 decimals) for metrics at the selected timestamp
- **Component Tabs**: Metrics are grouped by component type; opens on the graph's current tab when grouped by component type
- **Disabled Metrics Hidden**: Metrics disabled in the configuration are not listed
- **Process Metrics**: The PROCESS tab shows each process as a card of its fields (not drawn on the graph)
- **Formatted Timestamp**: Human-readable date/time
- **Scrollable List**: Handles large numbers of metrics

### Loading & Error States
- **Loading Spinner**: Shows animated spinner while fetching data
- **Error Messages**: Displays error messages when data fetch fails
- **Empty State**: Shows helpful message when no data is available for selected range

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation

```bash
cd react
npm install
```

### Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:5173` (or the port specified in vite.config.ts).

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## API Integration

See the endpoint list below.

## Components Structure

```
src/
├── components/
│   ├── ui/                      # shadcn/ui primitive components (Tailwind CSS)
│   │   ├── badge.tsx
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── checkbox.tsx
│   │   ├── input.tsx
│   │   ├── label.tsx
│   │   └── separator.tsx
│   ├── TimeRangePicker.tsx      # Date/time range, present mode, preset durations, reset
│   ├── MetricsGraph.tsx         # D3.js line graph with series selector and drag-to-zoom
│   ├── ConfigurationSection.tsx # Metric enable/disable, color, order, filter, sort
│   └── MetricPopup.tsx          # Metric values popup at selected timestamp
├── hooks/
│   └── useMetricsAPI.ts         # API client hook with axios (metrics, metadata, configs), unit conversion
├── lib/
│   └── utils.ts                 # Utility functions (cn helper for Tailwind classes)
├── App.tsx                      # Main application component orchestrating all features
└── main.tsx                     # React entry point
```

## API Integration

The UI connects to the FastAPI backend through these endpoints:

- `GET /api/metrics/range` - Fetch metrics within a datetime range (`start_datetime`, `end_datetime`, `bucket_count`); returns batches without metadata
- `GET /api/metrics/metadata` - Retrieve all metric metadata (raw `name`, type, unit, alias, description, component type, thresholds); joined with range data on the frontend by `name`
- `GET /api/metrics/config` - Retrieve saved metric configurations
- `POST /api/metrics/config` - Save/update metric configurations

## Technology Stack

- **React 19** - UI framework
- **TypeScript 6** - Type-safe development
- **Vite 8** - Build tool and dev server
- **Tailwind CSS 4** - Utility-first CSS framework
- **shadcn/ui** - Component primitives built on Radix UI
- **D3.js 7** - Graph rendering
- **Axios** - HTTP client
- **date-fns** - Date formatting
- **Lucide React** - Icons

## Development Workflow

### Start Backend Server First
Ensure the FastAPI backend is running on `http://127.0.0.1:5000` before starting the frontend dev server. The Vite dev server proxies `/api` requests to the backend.

### Run Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

The dev server proxies `/api` (and `/websocket`) to the FastAPI backend at port 5000.

Lint with `npm run lint`.

### Build for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

Preview the production build locally before deploying.

## Configuration Files

- `metric_config.json` - Stored in the project root, contains user-saved metric configurations
- `metadata/metric_metadata.json` - Contains all available metrics with their metadata

## Styling

The UI uses Tailwind CSS with custom shadcn/ui theming. Colors are defined in `src/index.css` using CSS variables for easy customization.

## Data Flow

1. User selects time range → API fetches metrics data
2. Metrics are processed and displayed on D3 graph
3. User clicks graph point → Popup shows exact values
4. User modifies configuration → Changes saved to backend
5. Configuration changes update which metrics appear on graph

## Notes

- Metrics with component type PROCESS are excluded from graphs (shown only in the popup); metrics with "count" or "total_bytes" in the name are hidden from the configuration list
- GPU metrics named `cardN_*` are split into per-card component types (e.g. `GPU 0`)
- Configs and series are keyed by raw metric name; the alias is display-only
- If no metric configurations exist yet, all metrics fetched from `/metrics/metadata` are enabled by default with preset colors

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
