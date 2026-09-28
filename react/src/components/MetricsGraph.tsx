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
    const [dimensions, setDimensions] = useState({ width: 800, height: 400 })

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

        // Y scale (value)
        const maxValue = Math.max(...series.flatMap((s) => s.data.map((d) => d.value))) || 100
        const minValue = Math.min(...series.flatMap((s) => s.data.map((d) => d.value))) || 0
        const y = d3.scaleLinear()
            .domain([minValue * 0.9, maxValue * 1.1])
            .range([height, 0])

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

        // Add title
        g.append('text')
            .attr('x', width / 2)
            .attr('y', -10)
            .attr('text-anchor', 'middle')
            .style('font-size', '14px')
            .style('font-weight', 'bold')
            .text('Metrics Over Time')

        // Add Y axis label
        g.append('text')
            .attr('transform', `rotate(-90)`)
            .attr('x', -height / 2)
            .attr('y', -width / 2 + 40)
            .attr('text-anchor', 'middle')
            .style('font-size', '12px')
            .style('fill', '#666')
            .text('Metric Value')

        // Draw lines for each series
        series.forEach((seriesItem, index) => {
            const lineData = seriesItem.data.map((d) => ({
                x: x(new Date(d.timestamp).getTime()),
                y: y(d.value),
            }))

            const lineGenerator = d3.line<MetricDataPoint>()
                .x((d: MetricDataPoint) => d.x)
                .y((d: MetricDataPoint) => d.y)
                .curve(d3.curveMonotoneX)
                .defined((d: MetricDataPoint) => !Number.isNaN(d.x) && !Number.isNaN(d.y))

            g.append('path')
                .datum(lineData)
                .attr('fill', 'none')
                .attr('stroke', colorScale(seriesItem.name))
                .attr('stroke-width', 2)
                .attr('stroke-linejoin', 'round')
                .attr('stroke-linecap', 'round')
                .attr('d', lineGenerator)

            // Add points that are clickable
            lineData.forEach((point: { x: number; y: number }, i: number) => {
                g.append('circle')
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
                    .on('mouseover', (_event: any, d: MetricDataPoint) => {
                        d3.select(_event.currentTarget)
                            .transition()
                            .duration(200)
                            .attr('r', 6)
                    })
                    .on('mouseout', (_event: any, d: MetricDataPoint) => {
                        d3.select(_event.currentTarget)
                            .transition()
                            .duration(200)
                            .attr('r', 4)
                    })
            })

            // Add legend for each series
            g.append('g')
                .attr('transform', `translate(${width - 150}, ${index === 0 ? 20 : 40})`)
                .append('rect')
                .attr('x', 0)
                .attr('y', 0)
                .attr('width', 140)
                .attr('height', 20)
                .style('fill', '#fff')
                .style('stroke', '#ddd')

            g.append('line')
                .attr('x1', 0)
                .attr('y1', 10)
                .attr('x2', 140)
                .attr('y2', 10)
                .attr('stroke', colorScale(seriesItem.name))
                .attr('stroke-width', 2)

            g.append('text')
                .attr('x', 145)
                .attr('y', 14)
                .style('font-size', '11px')
                .style('fill', colorScale(seriesItem.name))
                .text(seriesItem.name)
        })

        return () => {
            svg.selectAll('*').remove()
        }
    }, [series, dimensions, onClickTimePoint])

    return (
        <Card className="p-4">
            <svg ref={svgRef} width="100%" height={dimensions.height} style={{ minHeight: '400px' }} />
        </Card>
    )
}

interface MetricDataPoint {
    x: number
    y: number
}
