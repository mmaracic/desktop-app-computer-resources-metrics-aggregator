import { X } from 'lucide-react'
import { Button } from './ui/button'
import { Card } from './ui/card'
import { Badge } from './ui/badge'

interface MetricValue {
    readonly name: string
    readonly value: number | string
}

interface PopupProps {
    readonly isOpen: boolean
    readonly onClose: () => void
    readonly timestamp: string
    readonly metrics: MetricValue[]
}

export function MetricPopup({ isOpen, onClose, timestamp, metrics }: PopupProps) {
    if (!isOpen) return null

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString('en-US', {
            dateStyle: 'long',
            timeStyle: 'medium',
        })
    }

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-[600px] max-w-full p-6 shadow-xl">
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

                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                    {metrics.map((metric) => (
                        <div key={metric.name} className="flex items-center justify-between p-3 rounded-lg border">
                            <div className="flex items-center gap-2">
                                <Badge variant="outline" className="text-xs">
                                    {metric.name}
                                </Badge>
                            </div>
                            <div className="text-right">
                                <p className="font-semibold text-lg">{typeof metric.value === 'number' ? metric.value.toFixed(2) : metric.value}</p>
                                <p className="text-xs text-muted-foreground">Value</p>
                            </div>
                        </div>
                    ))}
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
