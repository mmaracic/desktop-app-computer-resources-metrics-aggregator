import { useState } from 'react'
import { Trash2, ArrowUp, ArrowDown } from 'lucide-react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Checkbox } from './ui/checkbox'
import { Card } from './ui/card'
import { Separator } from './ui/separator'
import { OTHER_TYPE } from '../lib/utils'

interface MetricConfig {
    name: string
    enabled: boolean
    order: number
    color: string
}

interface AvailableMetric {
    name: string
    alias?: string
    description?: string
    componentType?: string
}

interface ConfigurationSectionProps {
    configs: MetricConfig[]
    onChange: (configs: MetricConfig[]) => void
    onSave: (configs: MetricConfig[]) => void
    availableMetrics?: AvailableMetric[]
    isDefault?: boolean
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
    '#14b8a6',
    '#0ea5e9',
    '#a855f7',
    '#ec4899',
    '#eab308',
    '#22c55e',
    '#64748b',
    '#78716c',
    '#000000',
    '#ffffff',
]

export function ConfigurationSection({ configs, onChange, onSave, availableMetrics, isDefault = false }: Readonly<ConfigurationSectionProps>) {
    const [searchTerm, setSearchTerm] = useState('')
    const [selectedTypes, setSelectedTypes] = useState<string[]>([])
    const [sortBy, setSortBy] = useState<'order' | 'type-name'>('order')

    const localConfigs = configs || []

    // Join each config metric with its metadata by name to get its type
    const metadataByName = new Map((availableMetrics || []).map((m) => [m.name, m]))
    const joinedConfigs = localConfigs.map((c) => ({
        ...c,
        alias: metadataByName.get(c.name)?.alias || c.name,
        componentType: metadataByName.get(c.name)?.componentType || OTHER_TYPE,
    }))
    const allTypes = Array.from(new Set(joinedConfigs.filter((c) => !!c.name).map((c) => c.componentType))).sort(
        (a, b) => a.localeCompare(b, undefined, { numeric: true }),
    )

    const toggleType = (type: string) =>
        setSelectedTypes((prev) => (prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]))

    // Filter out process metrics (metrics with "count" or "total_bytes" in name are typically not shown)
    const visibleConfigs = joinedConfigs.filter(
        (config) => !!config.name && !config.name.includes('count') && !config.name.includes('total_bytes')
    )

    // Further filter by alias or name (case-insensitive substring match)
    const nameFiltered = searchTerm.trim()
        ? visibleConfigs.filter((config) => `${config.alias} ${config.name}`.toLowerCase().includes(searchTerm.trim().toLowerCase()))
        : visibleConfigs

    const typeFiltered = selectedTypes.length > 0
        ? nameFiltered.filter((config) => selectedTypes.includes(config.componentType))
        : nameFiltered

    const displayMetrics = sortBy === 'type-name'
        ? [...typeFiltered].sort(
            (a, b) => a.componentType.localeCompare(b.componentType) || a.alias.localeCompare(b.alias),
        )
        : typeFiltered

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

                <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm text-muted-foreground">Type:</span>
                    {allTypes.map((type) => (
                        <Button
                            key={type}
                            size="sm"
                            variant="outline"
                            aria-pressed={selectedTypes.includes(type)}
                            className={selectedTypes.includes(type) ? 'bg-blue-600 text-white border-blue-600 hover:bg-blue-700 hover:text-white' : ''}
                            onClick={() => toggleType(type)}
                        >
                            {type}
                        </Button>
                    ))}
                    {selectedTypes.length > 0 && (
                        <Button size="sm" variant="ghost" onClick={() => setSelectedTypes([])}>
                            Clear
                        </Button>
                    )}
                    <span className="text-sm text-muted-foreground ml-auto">Sort by:</span>
                    <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value as 'order' | 'type-name')}
                        className="h-8 rounded-md border border-input bg-transparent px-2 text-sm"
                    >
                        <option value="order">Order</option>
                        <option value="type-name">Type, then name</option>
                    </select>
                </div>
                <div className="space-y-3 max-h-[640px] overflow-y-auto pr-1">
                    {displayMetrics.map((config, index) => (
                        <Card key={`${config.name}-${index}`} className="p-4 border-l-4" style={{ borderLeftColor: config.color }}>
                            <div className="flex items-center gap-4">
                                {/* Enable/Disable Checkbox */}
                                <div className="flex items-center gap-2">
                                    <Checkbox
                                        checked={config.enabled}
                                        onCheckedChange={() => handleToggleEnabled(config.name)}
                                    />
                                    <span className={`font-medium ${!config.enabled ? 'text-muted-foreground line-through' : ''}`}>
                                        {config.alias}
                                    </span>
                                </div>

                                {/* Color Picker */}
                                <div className="flex items-center gap-2 flex-1 min-w-0">
                                    <span className="text-sm text-muted-foreground">Color:</span>
                                    <div className="flex gap-1 flex-wrap items-center flex-1 min-w-0">
                                        {presetColors.map((color) => (
                                            <button
                                                key={color}
                                                onClick={() => handleColorChange(config.name, color)}
                                                className={`w-6 h-6 rounded-full border-2 ${config.color === color ? 'border-gray-900' : 'border-transparent'}`}
                                                style={{ backgroundColor: color }}
                                                title={color}
                                            />
                                        ))}
                                        <div className="flex items-center gap-2 ml-2 pl-3 border-l">
                                            <span className="text-xs text-muted-foreground">Custom:</span>
                                            <input
                                                type="color"
                                                value={/^#[0-9a-f]{6}$/i.test(config.color) ? config.color : '#000000'}
                                                onChange={(e) => handleColorChange(config.name, e.target.value)}
                                                className="w-8 h-8 p-0.5 border rounded cursor-pointer bg-transparent"
                                                title="Pick a custom RGB color"
                                            />
                                        </div>
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
                                <span title={isDefault ? 'Default configuration cannot be deleted' : 'Remove'} className={isDefault ? 'cursor-not-allowed' : ''}>
                                    <Button onClick={() => handleRemoveMetric(config.name)} size="icon" variant="ghost" disabled={isDefault} className={`h-8 w-8 ${isDefault ? 'text-gray-400 opacity-40' : 'text-red-500 hover:text-red-700'}`}>
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </span>
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
