import { useEffect, useState } from 'react'
import { useMetricsAPI, type MetricData, type MetricConfig } from './hooks/useMetricsAPI'
import { TimeRangePicker } from './components/TimeRangePicker'
import { MetricsGraph } from './components/MetricsGraph'
import { ConfigurationSection } from './components/ConfigurationSection'
import { MetricPopup } from './components/MetricPopup'
import { Card } from './components/ui/card'

const API_BASE_URL = '/api'

function App() {
  const { getMetricsByRange, getMetricMetadata, getMetricConfigs, saveMetricConfigs, joinMetadataWithMetrics } = useMetricsAPI()

  const [metricsData, setMetricsData] = useState<MetricData[]>([])
  const [configs, setConfigs] = useState<MetricConfig[]>([])
  const [availableMetrics, setAvailableMetrics] = useState<Array<{ name: string; description?: string; componentType?: string }>>([])
  const [selectedTimestamp, setSelectedTimestamp] = useState<string | null>(null)
  const [selectedMetrics, setSelectedMetrics] = useState<Array<{ name: string; value: unknown; description?: string; componentType?: string }>>([])
  const [isLoading, setIsLoading] = useState(true)
  const [graphType, setGraphType] = useState<string>('')
  const [activeTab, setActiveTab] = useState<'graph' | 'config'>('graph')
  const [loadedFromFile, setLoadedFromFile] = useState(false)
  const [theme, setTheme] = useState<'system' | 'light' | 'dark'>(
    () => {
      try {
        return (localStorage.getItem('theme') as 'system' | 'light' | 'dark') || 'system'
      } catch {
        return 'system'
      }
    }
  )

  useEffect(() => {
    try {
      localStorage.setItem('theme', theme)
    } catch {
      // localStorage is unavailable in pywebview private mode
    }
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const apply = () => {
      const dark = theme === 'dark' || (theme === 'system' && media.matches)
      document.documentElement.classList.toggle('dark', dark)
    }
    apply()
    media.addEventListener('change', apply)
    return () => media.removeEventListener('change', apply)
  }, [theme])
  const [error, setError] = useState<string | null>(null)

  // Time range state
  const [currentStartDate, setCurrentStartDate] = useState<string>('')
  const [currentEndDate, setCurrentEndDate] = useState<string>('')
  const [bucketCount, setBucketCount] = useState<number>(100)

  // Time range formatting helper
  const formatISOWithTZ = (date: Date): string => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')
    const tzOffset = date.getTimezoneOffset() * 60000
    const tzSign = tzOffset >= 0 ? '-' : '+'
    const tzHours = String(Math.abs(tzOffset / 3600000)).padStart(2, '0')
    const tzMinutes = String(Math.abs((tzOffset % 3600000) / 60000)).padStart(2, '0')
    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}${tzSign}${tzHours}:${tzMinutes}`
  }

  const now = new Date()
  const twentyFourHoursAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000)

  // Fetch all data on mount or when time range changes
  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // Use current time range if set, otherwise default to last 24 hours
        const startDatetime = currentStartDate || formatISOWithTZ(twentyFourHoursAgo)
        const endDatetime = currentEndDate || formatISOWithTZ(now)

        console.log('📡 Fetching metrics from:', `${API_BASE_URL}/metrics/range`)
        console.log('   Params:', { start_datetime: startDatetime, end_datetime: endDatetime })

        // Fetch metadata first (needed for joining with metrics)
        const metadata = await getMetricMetadata()
        console.log('✅ Metadata loaded:', metadata.size, 'metrics')
        console.log('   Sample metadata keys:', Array.from(metadata.keys()).slice(0, 5))

        // Convert metadata Map to array format for ConfigurationSection
        const metricsList = Array.from(metadata.values()).map(meta => ({
          name: meta.alias,
          description: meta.description,
          componentType: meta.component_type,
        }))
        console.log('✅ Available metrics list:', metricsList.length, 'items')
        console.log('   Sample metrics:', metricsList.slice(0, 3))
        setAvailableMetrics(metricsList)

        const rawMetricsData = await getMetricsByRange(startDatetime, endDatetime, undefined, bucketCount)
        console.log('✅ Received raw metrics data:', rawMetricsData.length, 'batches')
        if (rawMetricsData.length > 0) {
          console.log('   First batch has', rawMetricsData[0].metrics.length, 'metrics')
          console.log('   Sample metric names:', rawMetricsData[0].metrics.slice(0, 5).map(m => m.name))
        }
        console.log('   Type of rawMetricsData:', typeof rawMetricsData)
        console.log('   Is Array?', Array.isArray(rawMetricsData))

        // Join metadata with metrics on frontend
        const enrichedMetricsData = joinMetadataWithMetrics(rawMetricsData, metadata)
        console.log('✅ Metrics enriched with metadata')
        console.log('   Enriched data has', enrichedMetricsData.length, 'batches')
        if (enrichedMetricsData.length > 0) {
          console.log('   First batch has', enrichedMetricsData[0].metrics.length, 'metrics')
          console.log('   Sample enriched metrics:', enrichedMetricsData[0].metrics.slice(0, 3).map(m => ({ name: m.name, value: m.value })))
        }
        setMetricsData(enrichedMetricsData)
      } catch (err: any) {
        setError(`Failed to fetch data: ${err.message}`)
        console.error('❌ Error fetching data:', err)
        console.error('Stack trace:', err.stack)
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [currentStartDate, currentEndDate, bucketCount])

  // Fetch configurations on mount
  useEffect(() => {
    const fetchConfigs = async () => {
      try {
        console.log('📡 Fetching configs from:', `${API_BASE_URL}/metrics/config`)
        let configData: MetricConfig[] = []

        try {
          configData = await getMetricConfigs()
        } catch (err) {
          console.warn('⚠️ Could not fetch configs, using defaults:', err)
        }

        // Ensure we always have an array
        if (!Array.isArray(configData)) {
          console.warn('⚠️ Configs response is not an array, using defaults. Got:', typeof configData, configData)
          configData = []
        }

        console.log('✅ Received configs:', configData.length, 'items')
        if (configData.length > 0) {
          console.log('   Sample configs:', configData.slice(0, 3).map(c => ({ name: c.name, enabled: c.enabled, color: c.color })))
        }
        setConfigs(configData)
        setLoadedFromFile(configData.length > 0)
      } catch (err: any) {
        console.error('❌ Error fetching configs:', err)
        console.error('Stack trace:', err.stack)
        // Set empty array on error so UI doesn't break
        setConfigs([])
      }
    }

    fetchConfigs()
  }, [])

  const presetColors = [
    '#ef4444', '#f97316', '#f59e0b', '#84cc16', '#10b981',
    '#06b6d4', '#3b82f6', '#6366f1', '#8b5cf6', '#d946ef', '#f43f5e',
  ]

  // Any available metric without a saved config defaults to enabled with a preset color.
  // This mirrors ConfigurationSection's local defaulting so the graph and config UI stay in sync.
  const effectiveConfigs: MetricConfig[] = (() => {
    const existingConfigs = Array.isArray(configs) ? configs : []
    const missingMetrics = availableMetrics.filter(
      (meta) => !existingConfigs.some((c) => c.name === meta.name)
    )
    const defaultsForMissing = missingMetrics.map((meta, index) => ({
      name: meta.name,
      enabled: true,
      order: existingConfigs.length + index,
      color: presetColors[(existingConfigs.length + index) % presetColors.length],
    }))
    return [...existingConfigs, ...defaultsForMissing]
  })()

  // Process metrics data for graph
  const enabledMetrics = effectiveConfigs.filter((c) => c.enabled)

  // Group metrics by name to create time series with all data points
  const metricsBySeries: Record<string, { color: string; componentType: string; data: Array<{ timestamp: string; value: number }> }> = {}

  if (metricsData.length > 0) {
    metricsData.forEach((timeBatch) => {
      timeBatch.metrics.forEach((metric) => {
        // Configs are keyed by alias (from metadata), not the raw technical metric name
        const seriesName = metric.metadata?.alias || metric.name
        const config = enabledMetrics.find((c) => c.name === seriesName)
        const componentType = metric.metadata?.component_type || 'OTHER'
        if (config && componentType !== 'PROCESS' && typeof metric.value === 'number') {
          if (!metricsBySeries[seriesName]) {
            metricsBySeries[seriesName] = {
              color: config.color,
              componentType,
              data: [],
            }
          }
          metricsBySeries[seriesName].data.push({
            timestamp: timeBatch.stored_at,
            value: metric.value,
          })
        }
      })
    })
  }

  // Convert grouped metrics to series array with names
  const allSeries = Object.entries(metricsBySeries).map(([name, data]) => ({
    name,
    ...data,
  }))
  const componentTypes = Array.from(new Set(allSeries.map((s) => s.componentType)))
  const currentType = componentTypes.includes(graphType) ? graphType : componentTypes[0]
  const series = allSeries.filter((s) => s.componentType === currentType)

  // Get all metrics (enabled + disabled) for popup at a specific timestamp
  const getAllMetricsAtTimestamp = (timestamp: string): Array<{ name: string; value: unknown; description?: string; componentType?: string }> => {
    const batch = metricsData.find((m) => m.stored_at === timestamp)
    if (!batch) return []

    // Return all metrics from the batch, not just enabled ones
    return batch.metrics.map(m => ({
      name: m.metadata?.alias || m.name,
      description: m.metadata?.description,
      componentType: m.metadata?.component_type,
      value: m.value,
    }))
  }

  const handleTimePointClick = (timestamp: string) => {
    setSelectedTimestamp(timestamp)
    const allMetrics = getAllMetricsAtTimestamp(timestamp)
    setSelectedMetrics(allMetrics)
  }

  const handleConfigSave = async (newConfigs: MetricConfig[]) => {
    try {
      await saveMetricConfigs(newConfigs)
      setConfigs(newConfigs)
      setLoadedFromFile(true)
    } catch (err) {
      console.error('Failed to save configs:', err)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="w-full p-6 space-y-6">
        <div className="flex gap-2 border-b">
          {([['graph', 'Graph'], ['config', 'Configuration']] as const).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`px-4 py-2 -mb-px border-b-2 font-medium ${activeTab === key ? 'border-primary text-foreground' : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
            >
              {label}
            </button>
          ))}
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value as 'system' | 'light' | 'dark')}
            className="ml-auto mb-1 rounded-md border bg-background text-foreground px-2 text-sm"
            aria-label="Theme"
          >
            <option value="system">System</option>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </div>

        {activeTab === 'graph' && (<>
          {/* Time Range Section */}
          <Card className="px-4 py-3">
            <TimeRangePicker
              onTimeRangeChange={(start, end) => {
                setCurrentStartDate(start)
                setCurrentEndDate(end)
              }}
              extra={
                <div className="flex items-center gap-2 text-xs">
                  <label htmlFor="bucket-count">Buckets</label>
                  <select
                    id="bucket-count"
                    value={bucketCount}
                    onChange={(e) => setBucketCount(Number(e.target.value))}
                    className="h-8 rounded-md border bg-background text-foreground px-2"
                  >
                    {[100, 250, 500, 1000].map((n) => (
                      <option key={n} value={n}>{n}</option>
                    ))}
                  </select>
                </div>
              }
            />
          </Card>

          {/* Graph Section */}
          <Card className="p-6">
            <div className="mb-4">
              <p className="text-sm text-muted-foreground">
                Click on any point in the graph to see detailed values. Hover over point to see its value.
              </p>
              <p>
                Hover over line to scale the Y axis according to it. Leave the graph to restore Y scale.
              </p>
            </div>

            {componentTypes.length > 0 && (
              <div className="flex flex-wrap gap-2 border-b mb-4">
                {componentTypes.map((type) => (
                  <button
                    key={type}
                    onClick={() => setGraphType(type)}
                    className={`px-3 py-1 -mb-px border-b-2 text-sm font-medium rounded-t-md ${currentType === type ? 'border-[hsl(var(--primary))] bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]' : 'border-transparent text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--muted))]'}`}
                  >
                    {type}
                  </button>
                ))}
              </div>
            )}

            {isLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : series.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                {error || 'No data available for the selected time range'}
              </div>
            ) : null}

            {!isLoading && series.length > 0 && (
              <MetricsGraph series={series} onClickTimePoint={handleTimePointClick} />
            )}
          </Card>
        </>)}

        {activeTab === 'config' && (
          <Card className="p-6">
            <ConfigurationSection
              configs={effectiveConfigs}
              onChange={setConfigs}
              onSave={handleConfigSave}
              isDefault={!loadedFromFile}
              availableMetrics={availableMetrics}
            />
          </Card>
        )}

        {/* Popup for selected time point */}
        {selectedTimestamp && (
          <MetricPopup
            isOpen={!!selectedTimestamp}
            onClose={() => setSelectedTimestamp(null)}
            timestamp={selectedTimestamp}
            metrics={selectedMetrics}
            initialTab={currentType}
          />
        )}
      </div>
    </div>
  )
}

export default App
