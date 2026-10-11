import { useMemo, useState } from 'react'
import { X } from 'lucide-react'
import { Button } from './ui/button'
import { Card } from './ui/card'
import { Badge } from './ui/badge'

interface MetricValue {
    readonly name: string
    readonly value: unknown
    readonly description?: string
    readonly componentType?: string
}

interface PopupProps {
    readonly isOpen: boolean
    readonly onClose: () => void
    readonly timestamp: string
    readonly metrics: MetricValue[]
    readonly initialTab?: string
}

const PROCESS_TYPE = 'PROCESS'
const OTHER_TYPE = 'OTHER'

// Values may be objects/arrays, which React cannot render directly.
const formatValue = (value: unknown): string => {
    if (typeof value === 'number') return value.toFixed(2)
    if (typeof value === 'string') return value
    return JSON.stringify(value) ?? String(value)
}

function ProcessCard({ metric }: { readonly metric: MetricValue }) {
    const fields =
        metric.value !== null && typeof metric.value === 'object'
            ? Object.entries(metric.value as Record<string, unknown>)
            : [['value', metric.value] as [string, unknown]]

    return (
        <div className="p-3 rounded-lg border bg-muted/40">
            <Badge variant="outline" className="text-xs mb-2" title={metric.description || undefined}>
                {metric.name}
            </Badge>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                {fields.map(([key, val]) => (
                    <div key={key} className="contents">
                        <dt className="text-muted-foreground text-left">{key}</dt>
                        <dd className="font-medium text-right break-all">{formatValue(val)}</dd>
                    </div>
                ))}
            </dl>
        </div>
    )
}

function MetricRow({ metric }: { readonly metric: MetricValue }) {
    return (
        <div className="flex items-center justify-between p-3 rounded-lg border">
            <Badge variant="outline" className="text-xs" title={metric.description || undefined}>
                {metric.name}
            </Badge>
            <div className="text-right">
                <p className="font-semibold text-lg">{formatValue(metric.value)}</p>
                <p className="text-xs text-muted-foreground">Value</p>
            </div>
        </div>
    )
}

export function MetricPopup({ isOpen, onClose, timestamp, metrics, initialTab }: PopupProps) {
    const [selectedTab, setSelectedTab] = useState<string | null>(initialTab ?? null)

    const groups = useMemo(() => {
        const map = new Map<string, MetricValue[]>()
        metrics.forEach((m) => {
            const type = m.componentType || OTHER_TYPE
            map.set(type, [...(map.get(type) ?? []), m])
        })
        return map
    }, [metrics])

    if (!isOpen) return null

    const tabs = Array.from(groups.keys())
    const activeTab = selectedTab && groups.has(selectedTab) ? selectedTab : tabs[0]
    const activeMetrics = activeTab ? (groups.get(activeTab) ?? []) : []

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString('en-US', {
            dateStyle: 'long',
            timeStyle: 'medium',
        })
    }

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-[600px] max-w-full p-6 shadow-xl" style={{ backgroundColor: 'hsl(var(--card))' }}>
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold">Metric Values</h2>
                    <Button onClick={onClose} size="icon" variant="ghost">
                        <X className="h-5 w-5" />
                    </Button>
                </div>

                <div className="mb-4 p-3 bg-muted rounded-lg">
                    <p className="text-sm text-muted-foreground">
                        Selected Time: <span className="font-medium">{formatDate(timestamp)}</span>
                    </p>
                </div>

                {tabs.length > 0 && (
                    <div className="flex flex-wrap gap-1 border-b mb-4">
                        {tabs.map((tab) => (
                            <button
                                key={tab}
                                onClick={() => setSelectedTab(tab)}
                                className={`px-3 py-1.5 -mb-px border-b-2 text-sm font-medium rounded-t-md ${activeTab === tab ? 'border-[hsl(var(--primary))] bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]' : 'border-transparent text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--muted))]'}`}
                            >
                                {tab}
                            </button>
                        ))}
                    </div>
                )}

                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                    {activeMetrics.map((metric, index) =>
                        activeTab === PROCESS_TYPE ? (
                            <ProcessCard key={`${metric.name}-${index}`} metric={metric} />
                        ) : (
                            <MetricRow key={`${metric.name}-${index}`} metric={metric} />
                        ),
                    )}
                </div>

                {metrics.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                        No metrics available for this time point
                    </div>
                )}
            </Card>
        </div>
    )
}
