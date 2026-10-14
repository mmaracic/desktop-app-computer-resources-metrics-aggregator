import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}
export const DEFAULT_PRESET_HOURS = 3
export const API_BASE_URL = '/api'
export const DEFAULT_BUCKET_COUNT = 100
export const PROCESS_TYPE = 'PROCESS'
export const OTHER_TYPE = 'OTHER'

// Backend expects full ISO 8601 with seconds and a UTC offset (e.g. 2026-09-28T00:31:00+02:00)
export const formatISOWithTZ = (date: Date): string => {
    const pad = (n: number) => String(n).padStart(2, '0')
    const offsetMin = -date.getTimezoneOffset()
    const sign = offsetMin >= 0 ? '+' : '-'
    const abs = Math.abs(offsetMin)
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}${sign}${pad(Math.floor(abs / 60))}:${pad(abs % 60)}`
}
