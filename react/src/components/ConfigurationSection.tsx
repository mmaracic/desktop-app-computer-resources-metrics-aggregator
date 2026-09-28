import { useState } from 'react'
import { Trash2, ArrowUp, ArrowDown } from 'lucide-react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Checkbox } from './ui/checkbox'
import { Card } from './ui/card'
import { Separator } from './ui/separator'

interface MetricConfig {
    name: string
    enabled: boolean
    order: number
    color: string
}

interface AvailableMetric {
    name: string
    description?: string
}

interface ConfigurationSectionProps {
    configs: MetricConfig[]
    onChange: (configs: MetricConfig[]) => void
    onSave: (configs: MetricConfig[]) => void
    availableMetrics?: AvailableMetric[]
}

const presetColors = [
    '#ef4444',
    '#f97316',
    '#f59e0b',
    '#84cc16',
    '#10b981',
    '#06b6d4',
    '#3b82f6',
    '#6366f1',
    '#8b5cf6',
    '#d946ef',
    '#f43f5e',
]

export function ConfigurationSection({ configs, onChange, onSave, availableMetrics }: Readonly<ConfigurationSectionProps>) {
    const [searchTerm, setSearchTerm] = useState('')

    console.log('[ConfigurationSection] Received configs:', configs?.length || 0, 'items')
    console.log('[ConfigurationSection] Available metrics:', availableMetrics?.length || 0, 'items')

    const localConfigs = configs || []

    // Filter out process metrics (metrics with "count" or "total_bytes" in name are typically not shown)
    const visibleConfigs = localConfigs.filter(
        (config) => !!config.name && !config.name.includes('count') && !config.name.includes('total_bytes')
    )

    // Further filter by the alias search term (case-insensitive substring match)
    const displayMetrics = searchTerm.trim()
        ? visibleConfigs.filter((config) => config.name.toLowerCase().includes(searchTerm.trim().toLowerCase()))
        : visibleConfigs

    const handleToggleEnabled = (name: string) => {
        onChange(localConfigs.map((c) => (c.name === name ? { ...c, enabled: !c.enabled } : c)))
    }

    const handleToggleAllEnabled = () => {
        onChange(localConfigs.map((c) => ({ ...c, enabled: !c.enabled })))
    }

    const handleColorChange = (name: string, color: string) => {
        onChange(localConfigs.map((c) => (c.name === name ? { ...c, color } : c)))
    }

    const handleOrderChange = (name: string, delta: number) => {
        const index = localConfigs.findIndex((c) => c.name === name)
        const newIndex = index + delta
        if (index === -1 || newIndex < 0 || newIndex >= localConfigs.length) return

        const newConfigs = [...localConfigs]
            ;[newConfigs[index], newConfigs[newIndex]] = [newConfigs[newIndex], newConfigs[index]]

        onChange(newConfigs.map((c, i) => ({ ...c, order: i })))
    }

    const handleRemoveMetric = (name: string) => {
        onChange(
            localConfigs
                .filter((c) => c.name !== name)
                .map((config, i) => ({ ...config, order: i })),
        )
    }

    const handleSave = () => {
        // Sort by order
        const sorted = [...localConfigs].sort((a, b) => a.order - b.order)
        onSave(sorted)
    }

    return (
        <Card className="p-6">
            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-semibold">Metric Configuration</h2>
                    <div className="flex items-center gap-2">
                        <Button onClick={handleToggleAllEnabled} variant="outline" size="sm">
                            Flip All Enabled
                        </Button>
                        <Button onClick={handleSave} variant="default" size="sm">
                            Save Configuration
                        </Button>
                    </div>
                </div>

                <Separator />

                {/* Filter configured metrics by alias */}
                <Input
                    placeholder="Filter metrics by name..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />

                {/* Metrics list - each metric gets its own card, scrolls after ~10 items */}
                <div className="space-y-3 max-h-[640px] overflow-y-auto pr-1">
                    {displayMetrics.map((config) => (
                        <Card key={config.name} className="p-4 border-l-4" style={{ borderLeftColor: config.color }}>
                            <div className="flex items-center gap-4">
                                {/* Enable/Disable Checkbox */}
                                <div className="flex items-center gap-2">
                                    <Checkbox
                                        checked={config.enabled}
                                        onCheckedChange={() => handleToggleEnabled(config.name)}
                                    />
                                    <span className={`font-medium ${!config.enabled ? 'text-muted-foreground line-through' : ''}`}>
                                        {config.name}
                                    </span>
                                </div>

                                {/* Color Picker */}
                                <div className="flex items-center gap-2">
                                    <span className="text-sm text-muted-foreground">Color:</span>
                                    <div className="flex gap-1">
                                        {presetColors.slice(0, 5).map((color) => (
                                            <button
                                                key={color}
                                                onClick={() => handleColorChange(config.name, color)}
                                                className={`w-6 h-6 rounded-full border-2 ${config.color === color ? 'border-gray-900' : 'border-transparent'}`}
                                                style={{ backgroundColor: color }}
                                                title={color}
                                            />
                                        ))}
                                    </div>
                                </div>

                                {/* Order Controls */}
                                <div className="flex items-center gap-1">
                                    <Button onClick={() => handleOrderChange(config.name, -1)} size="icon" variant="ghost" className="h-8 w-8">
                                        <ArrowUp className="h-4 w-4" />
                                    </Button>
                                    <span className="text-sm text-muted-foreground w-8 text-center">
                                        {config.order + 1}
                                    </span>
                                    <Button onClick={() => handleOrderChange(config.name, 1)} size="icon" variant="ghost" className="h-8 w-8">
                                        <ArrowDown className="h-4 w-4" />
                                    </Button>
                                </div>

                                {/* Remove Button */}
                                <Button onClick={() => handleRemoveMetric(config.name)} size="icon" variant="ghost" className="h-8 w-8 text-red-500 hover:text-red-700">
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </div>
                        </Card>
                    ))}
                </div>

                {displayMetrics.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                        {searchTerm.trim() ? 'No metrics match your filter.' : 'No metrics configured. Add a metric to get started.'}
                    </div>
                )}
            </div>
        </Card>
    )
}
