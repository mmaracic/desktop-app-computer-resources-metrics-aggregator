import { useState, useEffect, useRef } from 'react'
import { format, subHours } from 'date-fns'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Checkbox } from './ui/checkbox'
import { Separator } from './ui/separator'

interface TimeRangePickerProps {
    readonly onTimeRangeChange: (start: string, end: string) => void
}

type PresetDuration = '1h' | '3h' | '6h' | '12h' | '24h'

// Backend expects full ISO 8601 with seconds and a UTC offset (e.g. 2026-09-28T00:31:00+02:00)
const toISOWithOffset = (dateStr: string, timeStr: string): string => {
    if (!dateStr || !timeStr) return ''
    const local = new Date(`${dateStr}T${timeStr}:00`)
    const tzOffset = local.getTimezoneOffset() * 60000
    const tzSign = tzOffset >= 0 ? '-' : '+'
    const tzHours = String(Math.abs(tzOffset / 3600000)).padStart(2, '0')
    const tzMinutes = String(Math.abs((tzOffset % 3600000) / 60000)).padStart(2, '0')
    return `${dateStr}T${timeStr}:00${tzSign}${tzHours}:${tzMinutes}`
}

export function TimeRangePicker({ onTimeRangeChange }: TimeRangePickerProps) {
    const [startDate] = useState<string>('')
    const [endDate] = useState<string>('')
    const [startDateTime, setStartDateTime] = useState<{ date: string; time: string }>({ date: '', time: '' })
    const [endDateTime, setEndDateTime] = useState<{ date: string; time: string }>({ date: '', time: '' })
    const [isPresentSelected, setIsPresentSelected] = useState(true)
    const [resetDisabled, setResetDisabled] = useState(true)
    const [presetDuration, setPresetDuration] = useState<PresetDuration>('3h')

    const startDateRef = useRef<HTMLInputElement>(null)
    const startTimeRef = useRef<HTMLInputElement>(null)
    const endDateRef = useRef<HTMLInputElement>(null)
    const endTimeRef = useRef<HTMLInputElement>(null)

    useEffect(() => {
        const now = new Date()
        const defaultHours = 3 // Default to 3 hours when preset is checked

        const startDateObj = format(subHours(now, defaultHours), 'yyyy-MM-dd')
        const startTime = format(subHours(now, defaultHours), 'HH:mm')
        const endDateObj = format(now, 'yyyy-MM-dd')
        const endTime = format(now, 'HH:mm')

        setStartDateTime({ date: startDateObj, time: startTime })
        setEndDateTime({ date: endDateObj, time: endTime })
        setIsPresentSelected(true)
        setResetDisabled(true)
        setPresetDuration('3h')
    }, [])

    useEffect(() => {
        if (isPresentSelected) {
            const now = new Date()
            const hours = Number.parseInt(presetDuration.replace('h', ''), 10)
            const startDateObj = format(subHours(now, hours), 'yyyy-MM-dd')
            const startTime = format(subHours(now, hours), 'HH:mm')
            const endDateObj = format(now, 'yyyy-MM-dd')
            const endTime = format(now, 'HH:mm')

            // Update start date and time inputs when preset changes
            setStartDateTime({ date: startDateObj, time: startTime })
            setEndDateTime({ date: endDateObj, time: endTime })

            // Only call onTimeRangeChange without updating local state to avoid infinite loop
            onTimeRangeChange(
                toISOWithOffset(startDateObj, startTime),
                toISOWithOffset(endDateObj, endTime)
            )
        } else {
            const combinedStart = startDateTime.date && startDateTime.time ? toISOWithOffset(startDateTime.date, startDateTime.time) : startDate
            const combinedEnd = endDateTime.date && endDateTime.time ? toISOWithOffset(endDateTime.date, endDateTime.time) : endDate
            onTimeRangeChange(combinedStart, combinedEnd)
        }
    }, [isPresentSelected, presetDuration, startDateTime, endDateTime, startDate, endDate, onTimeRangeChange])

    const handleReset = () => {
        const now = new Date()
        const twentyFourHoursAgo = subHours(now, 24)

        const startDateObj = format(twentyFourHoursAgo, 'yyyy-MM-dd')
        const startTime = format(twentyFourHoursAgo, 'HH:mm')
        const endDateObj = format(now, 'yyyy-MM-dd')
        const endTime = format(now, 'HH:mm')

        setStartDateTime({ date: startDateObj, time: startTime })
        setEndDateTime({ date: endDateObj, time: endTime })
        setIsPresentSelected(true)
        setResetDisabled(true)
        onTimeRangeChange(toISOWithOffset(startDateObj, startTime), toISOWithOffset(endDateObj, endTime))
    }

    const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setStartDateTime(prev => ({ ...prev, date: e.target.value }))
        setResetDisabled(false)

        // Force update the input value after state change
        if (startDateRef.current) {
            startDateRef.current.value = e.target.value
        }
    }

    const handleStartTimeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setStartDateTime(prev => ({ ...prev, time: e.target.value }))
        setResetDisabled(false)

        // Force update the input value after state change
        if (startTimeRef.current) {
            startTimeRef.current.value = e.target.value
        }
    }

    const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setEndDateTime(prev => ({ ...prev, date: e.target.value }))
        setResetDisabled(false)

        // Force update the input value after state change
        if (endDateRef.current) {
            endDateRef.current.value = e.target.value
        }
    }

    const handleEndTimeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setEndDateTime(prev => ({ ...prev, time: e.target.value }))
        setResetDisabled(false)

        // Force update the input value after state change
        if (endTimeRef.current) {
            endTimeRef.current.value = e.target.value
        }
    }

    const handlePresentChange = () => {
        setIsPresentSelected(!isPresentSelected)
        setResetDisabled(false)
    }

    const handlePresetChange = (duration: PresetDuration) => {
        setPresetDuration(duration)
        setResetDisabled(true)
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <Label htmlFor="time-range">Time Range</Label>
                {!resetDisabled && (
                    <Button onClick={handleReset} variant="outline" size="sm">
                        Reset
                    </Button>
                )}
            </div>

            <div className="grid grid-cols-4 gap-3">
                <div className="space-y-1.5">
                    <Label htmlFor="start-date" className="text-xs">Start Date</Label>
                    <Input
                        ref={startDateRef}
                        id="start-date"
                        type="date"
                        value={startDateTime.date}
                        onChange={handleStartDateChange}
                    />
                </div>

                <div className="space-y-1.5">
                    <Label htmlFor="start-time" className="text-xs">Start Time</Label>
                    <Input
                        ref={startTimeRef}
                        id="start-time"
                        type="time"
                        value={startDateTime.time}
                        onChange={handleStartTimeChange}
                    />
                </div>

                <div className="space-y-1.5">
                    <Label htmlFor="end-date" className="text-xs">End Date</Label>
                    <Input
                        ref={endDateRef}
                        id="end-date"
                        type="date"
                        value={endDateTime.date}
                        onChange={handleEndDateChange}
                        disabled={isPresentSelected}
                    />
                </div>

                <div className="space-y-1.5">
                    <Label htmlFor="end-time" className="text-xs">End Time</Label>
                    <Input
                        ref={endTimeRef}
                        id="end-time"
                        type="time"
                        value={endDateTime.time}
                        onChange={handleEndTimeChange}
                        disabled={isPresentSelected}
                    />
                </div>
            </div>

            <div className="flex items-center space-x-2">
                <Checkbox
                    id="present"
                    checked={isPresentSelected}
                    onCheckedChange={handlePresentChange}
                />
                <Label htmlFor="present" className="cursor-pointer font-normal">
                    Show Present
                </Label>
            </div>

            {isPresentSelected && (
                <div className="space-y-2">
                    <Label htmlFor="preset-duration" className="text-xs">
                        Time Range:
                    </Label>
                    <select
                        id="preset-duration"
                        value={presetDuration}
                        onChange={(e) => handlePresetChange(e.target.value as PresetDuration)}
                        className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        <option value="1h">Last 1 hour</option>
                        <option value="3h">Last 3 hours</option>
                        <option value="6h">Last 6 hours</option>
                        <option value="12h">Last 12 hours</option>
                        <option value="24h">Last 24 hours</option>
                    </select>
                </div>
            )}

            <Separator />

            {isPresentSelected && (
                <p className="text-sm text-muted-foreground">
                    Showing the last {Number.parseInt(presetDuration.replace('h', ''), 10)} hour{Number.parseInt(presetDuration.replace('h', ''), 10) === 1 ? '' : 's'} of data
                </p>
            )}
            {!isPresentSelected && startDate && endDate && <TimeRangeDescription startDate={startDate} endDate={endDate} />}
        </div>
    )
}

function TimeRangeDescription({ startDate, endDate }: { readonly startDate: string; readonly endDate: string }) {
    const startDateTime = new Date(startDate)
    const endDateTime = new Date(endDate)

    const startFormatted = format(startDateTime, 'MMM dd, yyyy HH:mm')
    const endFormatted = format(endDateTime, 'MMM dd, yyyy HH:mm')

    return (
        <p className="text-sm text-muted-foreground">
            From {startFormatted} to {endFormatted}
        </p>
    )
}
