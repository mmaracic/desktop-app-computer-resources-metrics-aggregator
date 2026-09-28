# Computer Resources Metrics - React UI

This is the React frontend for the Computer Resources Metrics Aggregator application. It provides an interactive dashboard for visualizing computer resource metrics using D3.js graphs with a modern shadcn/ui design system built on Tailwind CSS.

## Features

### Time Range Picker
- **Date & Time Inputs**: Select custom start and end dates/times for metrics data
- **Present Checkbox**: When checked, automatically shows the last 24 hours of data (default)
- **Reset Button**: Resets all pickers to show the last 24 hours when "Present" is unchecked
- **Timezone-Aware**: Automatically adjusts timestamps based on local timezone offset
- Auto-refreshes graph data whenever time range changes

### Metrics Graph
- **D3.js Visualization**: Interactive line graphs with smooth curves showing metric trends over time
- **Multiple Metrics**: Displays all enabled metrics simultaneously with distinct colors
- **Clickable Data Points**: Click anywhere on the graph to see exact values at that timestamp
- **Hover Effects**: Data points enlarge on hover for better visibility and interaction
- **Smooth Curves**: Uses monotone X curve interpolation for clean line rendering
- **Dynamic Scales**: Automatically scales Y-axis based on data range (with 10% padding)
- **Responsive Layout**: Graph resizes to fit container dimensions

### Configuration Section
- **Enable/Disable Metrics**: Toggle visibility of individual metrics with checkboxes
- **Default to Enabled**: When no configuration exists, every available metric defaults to enabled
- **Color Selection**: Choose custom colors for each metric from a preset palette (11 colors)
- **Reordering**: Move metrics up/down using arrow buttons to change display order
- **Disable Metrics**: Toggle metrics off (they remain in configuration but hidden from graph)
- **Save Configuration**: Persist changes to `metric_config.json` in the metadata folder

### Popup Details
- **Exact Values**: Shows precise values for all metrics at selected timestamp
- **All Metrics Displayed**: Includes both enabled and disabled metrics in popup
- **Process Metrics**: Shows process-related metrics (not displayed on graph by default)
- **Formatted Timestamp**: Displays human-readable date/time format
- **Scrollable List**: Handles large numbers of metrics with scrollable container

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

The UI connects to the FastAPI backend through these endpoints:

- `GET /api/metrics/range` - Fetch metrics within a datetime range
- `GET /api/metrics/config` - Retrieve metric configurations
- `POST /api/metrics/config` - Save metric configurations

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
│   │   ├── separator.tsx
│   │   └── [more radix components]
│   ├── TimeRangePicker.tsx      # Date/time range selection with present checkbox
│   ├── MetricsGraph.tsx         # D3.js interactive line graph visualization
│   ├── ConfigurationSection.tsx # Metric enable/disable, color, order configuration
│   └── MetricPopup.tsx          # Detailed metric values popup at selected timestamp
├── hooks/
│   └── useMetricsAPI.ts         # API client hook with axios (metrics, metadata, configs)
├── lib/
│   └── utils.ts                 # Utility functions (cn helper for Tailwind classes)
├── App.tsx                      # Main application component orchestrating all features
└── main.tsx                     # React entry point
```

## API Integration

The UI connects to the FastAPI backend through these endpoints:

- `GET /api/metrics/range` - Fetch metrics within a datetime range (returns batches of metric data)
- `GET /api/metrics/metadata` - Retrieve all metric metadata (name, type, alias, description, thresholds)
- `GET /api/metrics/config` - Retrieve saved metric configurations
- `POST /api/metrics/config` - Save/update metric configurations

## Technology Stack

- **React 19** - UI framework with hooks-based architecture
- **TypeScript** - Type-safe development
- **Vite 8** - Fast build tool and dev server
- **Tailwind CSS 4** - Utility-first CSS framework
- **shadcn/ui** - Reusable component library built on Radix UI primitives
- **D3.js 7** - Data visualization for interactive graphs
- **Axios** - HTTP client for API requests
- **date-fns** - Date manipulation and formatting
- **Lucide React** - Beautiful, consistent icon library

## Development Workflow

### Start Backend Server First
Ensure the FastAPI backend is running on `http://127.0.0.1:5000` before starting the frontend dev server. The Vite dev server proxies `/api` requests to the backend.

### Run Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

The dev server automatically proxies API calls to the FastAPI backend at port 5000.

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

- `metric_config.json` - Stored in the `metadata/` folder, contains user-saved metric configurations
- `metric_metadata.json` - Contains all available metrics with their metadata

## Styling

The UI uses Tailwind CSS with custom shadcn/ui theming. Colors are defined in `src/index.css` using CSS variables for easy customization.

## Data Flow

1. User selects time range → API fetches metrics data
2. Metrics are processed and displayed on D3 graph
3. User clicks graph point → Popup shows exact values
4. User modifies configuration → Changes saved to backend
5. Configuration changes update which metrics appear on graph

## Notes

- Process metrics (those with "count" or "total_bytes" in name) are excluded from graphs and configuration
- All metric values are formatted appropriately for display
- The UI automatically handles loading states and errors
- Graph resizes responsively to container width
- If no metric configurations exist yet, all metrics fetched from `/metrics/metadata` are enabled by default

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
