import { useRef, useEffect, useState } from 'react'
// @ts-ignore - D3 types are complex and cause issues with strict mode
import * as d3 from 'd3'
import { Card } from './ui/card'

interface MetricSeries {
    name: string
    color: string
    data: Array<{ timestamp: string; value: number }>
}

interface GraphProps {
    series: MetricSeries[]
    onClickTimePoint: (timestamp: string) => void
}

interface GraphProps {
    series: MetricSeries[]
    onClickTimePoint: (timestamp: string) => void
}

export function MetricsGraph({ series, onClickTimePoint }: GraphProps) {
    const svgRef = useRef<SVGSVGElement>(null)
    const [dimensions, setDimensions] = useState({ width: 800, height: 500 })
    // Sticky until the cursor leaves the graph, so rescaling doesn't cause hover flicker
    const [activeSeries, setActiveSeries] = useState<string | null>(null)

    useEffect(() => {
        const handleResize = () => {
            if (svgRef.current) {
                const rect = svgRef.current.getBoundingClientRect()
                setDimensions({
                    width: rect.width,
                    height: rect.height,
                })
            }
        }

        handleResize()
        window.addEventListener('resize', handleResize)
        return () => window.removeEventListener('resize', handleResize)
    }, [])

    useEffect(() => {
        if (!svgRef.current || series.length === 0) return

        const svg = d3.select(svgRef.current)
        const margin = { top: 40, right: 30, bottom: 60, left: 80 }
        const width = dimensions.width - margin.left - margin.right
        const height = dimensions.height - margin.top - margin.bottom

        // Clear previous content
        svg.selectAll('*').remove()

        // Create SVG container
        const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

        // Parse timestamps and find time range
        const allTimestamps = series.flatMap((s) => s.data.map((d) => new Date(d.timestamp).getTime()))
        const minTime = Math.min(...allTimestamps)
        const maxTime = Math.max(...allTimestamps)

        // X scale (time)
        const x = d3.scaleTime()
            .domain([minTime, maxTime])
            .range([0, width])

        // Y scale (value), fitted to the hovered series when there is one
        const scaled = series.some((s) => s.name === activeSeries)
            ? series.filter((s) => s.name === activeSeries)
            : series
        const values = scaled.flatMap((s) => s.data.map((d) => d.value))
        const maxValue = Math.max(...values)
        const minValue = Math.min(...values)
        const pad = (maxValue - minValue) * 0.1 || Math.abs(maxValue) * 0.1 || 1
        const y = d3.scaleLinear()
            .domain([minValue - pad, maxValue + pad])
            .range([height, 0])

        svg.on('mouseleave', () => setActiveSeries(null))

        g.append('clipPath').attr('id', 'plot-clip')
            .append('rect').attr('x', -10).attr('y', 0).attr('width', width + 20).attr('height', height)
        const plot = g.append('g').attr('clip-path', 'url(#plot-clip)')

        // Color scale
        const colorScale = d3.scaleOrdinal()
            .domain(series.map((s) => s.name))
            .range(series.map((s) => s.color))

        // Add X axis
        g.append('g')
            .attr('transform', `translate(0,${height})`)
            .call(d3.axisBottom(x).ticks(5))
            .selectAll('text')
            .style('font-size', '12px')
            .style('fill', '#888')

        // Add Y axis
        g.append('g')
            .call(d3.axisLeft(y).ticks(5))
            .selectAll('text')
            .style('font-size', '12px')
            .style('fill', '#888')

        // Hover tooltip, positioned above the hovered element
        const tooltip = g.append('g').style('pointer-events', 'none').style('display', 'none')
        const tooltipBg = tooltip.append('rect').attr('rx', 4).attr('fill', '#222').attr('opacity', 0.9)
        const tooltipText = tooltip.append('text')
            .attr('text-anchor', 'middle')
            .style('font-size', '12px')
            .style('fill', '#fff')
        const showTooltip = (label: string, px: number, py: number, color: string) => {
            tooltip.style('display', null).raise()
            tooltipText.text(label).style('fill', '#fff')
            const w = (tooltipText.node() as SVGTextElement).getComputedTextLength() + 16
            tooltipBg.attr('width', w).attr('height', 22).attr('x', -w / 2).attr('y', -16).attr('stroke', color)
            tooltip.attr('transform', `translate(${px},${py - 14})`)
        }
        const hideTooltip = () => tooltip.style('display', 'none')

        // Draw lines for each series
        series.forEach((seriesItem) => {
            const lineData = seriesItem.data.map((d) => ({
                x: x(new Date(d.timestamp).getTime()),
                y: y(d.value),
            }))

            const lineGenerator = d3.line<MetricDataPoint>()
                .x((d: MetricDataPoint) => d.x)
                .y((d: MetricDataPoint) => d.y)
                .curve(d3.curveMonotoneX)
                .defined((d: MetricDataPoint) => !Number.isNaN(d.x) && !Number.isNaN(d.y))

            const dim = activeSeries !== null && scaled.length === 1 && seriesItem.name !== activeSeries

            plot.append('path')
                .datum(lineData)
                .attr('opacity', dim ? 0.25 : 1)
                .attr('fill', 'none')
                .attr('stroke', colorScale(seriesItem.name))
                .attr('stroke-width', 2)
                .attr('stroke-linejoin', 'round')
                .attr('stroke-linecap', 'round')
                .attr('d', lineGenerator)
                .style('cursor', 'pointer')
                .on('mouseenter', () => setActiveSeries(seriesItem.name))
                .on('mousemove', (event: any) => {
                    const [mx, my] = d3.pointer(event, g.node())
                    showTooltip(seriesItem.name, mx, my, seriesItem.color)
                })
                .on('mouseout', hideTooltip)

            // Always-visible label above the line's highest point
            const valid = lineData.filter((p: MetricDataPoint) => !Number.isNaN(p.x) && !Number.isNaN(p.y))
            if (valid.length > 0 && !dim) {
                const top = valid.reduce((a: MetricDataPoint, b: MetricDataPoint) => (b.y < a.y ? b : a))
                const label = g.append('text')
                    .attr('y', Math.max(top.y - 10, 10))
                    .style('font-size', '12px')
                    .style('font-weight', '600')
                    .style('pointer-events', 'none')
                    .style('fill', seriesItem.color)
                    .text(seriesItem.name)
                const labelWidth = (label.node() as SVGTextElement).getComputedTextLength()
                const lx = Math.min(Math.max(top.x - labelWidth / 2, 0), Math.max(width - labelWidth, 0))
                label.attr('x', lx)
            }

            // Add points that are clickable
            lineData.forEach((point: { x: number; y: number }, i: number) => {
                plot.append('circle')
                    .attr('opacity', dim ? 0.25 : 1)
                    .attr('cx', point.x)
                    .attr('cy', point.y)
                    .attr('r', 4)
                    .attr('fill', colorScale(seriesItem.name))
                    .attr('stroke', '#fff')
                    .attr('stroke-width', 1.5)
                    .style('cursor', 'pointer')
                    .on('click', () => {
                        onClickTimePoint(seriesItem.data[i].timestamp)
                    })
                    .on('mouseover', (_event: any) => {
                        setActiveSeries(seriesItem.name)
                        d3.select(_event.currentTarget).attr('r', 6)
                        showTooltip(String(seriesItem.data[i].value), point.x, point.y - 4, seriesItem.color)
                    })
                    .on('mouseout', (_event: any) => {
                        d3.select(_event.currentTarget).attr('r', 4)
                        hideTooltip()
                    })
            })
        })

        return () => {
            svg.selectAll('*').remove()
        }
    }, [series, dimensions, onClickTimePoint, activeSeries])

    return (
        <Card className="p-4">
            <svg ref={svgRef} width="100%" height={500} style={{ height: '500px', minHeight: '500px' }} />
        </Card>
    )
}

interface MetricDataPoint {
    x: number
    y: number
}
