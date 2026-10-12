import axios from 'axios'

const API_BASE_URL = '/api'

export interface MetricMetadata {
    name: string
    metric_type: string
    alias: string
    description: string
    component_type: string
    warning_threshold: number | null
    critical_threshold: number | null
}

export interface MetricData {
    stored_at: string
    metrics: Array<{
        name: string
        value: number | string
        metadata?: MetricMetadata
    }>
}

export interface MetricConfig {
    name: string
    enabled: boolean
    order: number
    color: string
}

const BYTES_PER_MB = 1024 * 1024

const convertUnits = (name: string, value: number | string): number | string => {
    if (typeof value !== 'number') return value
    if (name.endsWith('_milliwatts')) return value / 1000
    if (name.endsWith('_bytes') || name.startsWith('network_bytes_')) return value / BYTES_PER_MB
    return value
}

const convertAlias = (name: string, alias: string): string => {
    if (name.endsWith('_milliwatts')) return alias.replace(/\bmW\b/, 'W')
    if (name.endsWith('_bytes') || name.startsWith('network_bytes_')) {
        return alias.replace(/\bbytes\b/, 'MB')
    }
    return alias
}

const splitGpuType = (name: string, meta: MetricMetadata): MetricMetadata => {
    const card = /^card(\d+)_/.exec(name)
    return card && meta.component_type === 'GPU' ? { ...meta, component_type: `GPU ${card[1]}` } : meta
}

export const useMetricsAPI = () => {
    const getMetricsByRange = async (
        startDatetime: string,
        endDatetime: string,
        containerName?: string,
        bucketCount: number = 100
    ): Promise<MetricData[]> => {
        console.log('📡 [useMetricsAPI] Calling /api/metrics/range')
        console.log('   Params:', { start_datetime: startDatetime, end_datetime: endDatetime, container_name: containerName })
        try {
            const response = await axios.get<MetricData[]>(
                `${API_BASE_URL}/metrics/range`,
                {
                    params: {
                        start_datetime: startDatetime,
                        end_datetime: endDatetime,
                        bucket_count: bucketCount,
                        ...(containerName && { container_name: containerName }),
                    },
                }
            )
            console.log('✅ [useMetricsAPI] Received metrics data:', response.data.length, 'batches')

            // Ensure we always return an array (defensive check)
            const data = Array.isArray(response.data) ? response.data : []
            return data
        } catch (error: any) {
            console.error('❌ [useMetricsAPI] Error fetching metrics:', error.response?.data || error.message)
            throw error
        }
    }

    const getMetricMetadata = async (): Promise<Map<string, MetricMetadata>> => {
        console.log('📡 [useMetricsAPI] Calling /api/metrics/metadata')
        try {
            const response = await axios.get<MetricMetadata[]>(`${API_BASE_URL}/metrics/metadata`)
            console.log('✅ [useMetricsAPI] Received metadata:', response.data.length, 'items')

            // Convert array to Map for efficient lookup by the raw metric name (matches metric.name from /metrics/range)
            const metadataMap = new Map<string, MetricMetadata>()
            for (const meta of response.data) {
                metadataMap.set(meta.name, splitGpuType(meta.name, meta))
            }
            return metadataMap
        } catch (error: any) {
            console.error('❌ [useMetricsAPI] Error fetching metadata:', error.response?.data || error.message)
            throw error
        }
    }

    const getMetricConfigs = async (): Promise<MetricConfig[]> => {
        console.log('📡 [useMetricsAPI] Calling /api/metrics/config')
        try {
            const response = await axios.get<MetricConfig[]>(`${API_BASE_URL}/metrics/config`)
            console.log('✅ [useMetricsAPI] Received configs:', response.data.length, 'items')
            return response.data
        } catch (error: any) {
            console.error('❌ [useMetricsAPI] Error fetching configs:', error.response?.data || error.message)
            throw error
        }
    }

    const saveMetricConfigs = async (configs: MetricConfig[]): Promise<void> => {
        console.log('💾 [useMetricsAPI] Saving configs:', configs.length, 'items')
        try {
            await axios.post(`${API_BASE_URL}/metrics/config`, configs)
            console.log('✅ [useMetricsAPI] Configs saved successfully')
        } catch (error: any) {
            console.error('❌ [useMetricsAPI] Error saving configs:', error.response?.data || error.message)
            throw error
        }
    }

    // Helper to join metadata with metrics data
    const joinMetadataWithMetrics = (
        metricsData: MetricData[],
        metadataMap: Map<string, MetricMetadata>
    ): MetricData[] => {
        // Defensive check - ensure metricsData is an array
        if (!Array.isArray(metricsData)) {
            console.warn('⚠️ [joinMetadataWithMetrics] Received non-array metricsData:', typeof metricsData)
            return []
        }

        return metricsData.map(batch => ({
            ...batch,
            metrics: batch.metrics.map(metric => {
                // Get alias from metadata if available, otherwise use name
                const metricName = metric.name
                const existingMetadata = metric.metadata || metadataMap.get(metricName)

                const converted = existingMetadata
                    ? { ...splitGpuType(metricName, existingMetadata), alias: convertAlias(metricName, existingMetadata.alias) }
                    : undefined

                return {
                    ...metric,
                    value: convertUnits(metricName, metric.value),
                    metadata: converted || {
                        name: metricName,
                        metric_type: 'Unknown',
                        alias: metricName,
                        description: '',
                        component_type: 'Unknown',
                        warning_threshold: null,
                        critical_threshold: null,
                    },
                }
            }),
        }))
    }

    return {
        getMetricsByRange,
        getMetricMetadata,
        getMetricConfigs,
        saveMetricConfigs,
        joinMetadataWithMetrics,
    }
}
