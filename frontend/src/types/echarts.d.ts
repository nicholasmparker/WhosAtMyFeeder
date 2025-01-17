declare module 'vue-echarts' {
  import { DefineComponent } from 'vue'
  import type { ComposeOption } from 'echarts/core'
  
  const component: DefineComponent<{
    option: ComposeOption<any>
    theme?: string | object
    initOptions?: object
    autoresize?: boolean
    loading?: boolean
    loadingOptions?: object
    group?: string
    manualUpdate?: boolean
  }>
  
  export const THEME_KEY = 'echarts-theme'
  export default component
}

declare module 'echarts/core' {
  import * as echarts from 'echarts/core'
  export * from 'echarts/core'
  
  export type ComposeOption<
    T extends echarts.SeriesOption = echarts.SeriesOption
  > = echarts.ComposeOption<T>
  
  export const graphic: typeof echarts.graphic
  export { use } from 'echarts/core'
}

declare module 'echarts/charts' {
  import { LineChart, BarChart, HeatmapChart } from 'echarts/charts'
  export { LineChart, BarChart, HeatmapChart }
  
  interface BaseSeriesOption {
    name?: string
    type?: string
    data?: any[]
    smooth?: boolean
    symbol?: string
    symbolSize?: number
    emphasis?: {
      focus?: string
      itemStyle?: {
        color?: string | {
          type?: string
          x?: number
          y?: number
          x2?: number
          y2?: number
          colorStops?: Array<{
            offset: number
            color: string
          }>
        }
      }
    }
    lineStyle?: {
      width?: number
      type?: 'solid' | 'dashed' | 'dotted'
    }
    itemStyle?: {
      color?: string | {
        type?: string
        x?: number
        y?: number
        x2?: number
        y2?: number
        colorStops?: Array<{
          offset: number
          color: string
        }>
      }
    }
  }

  export interface LineSeriesOption extends BaseSeriesOption {
    type: 'line'
  }

  export interface BarSeriesOption extends BaseSeriesOption {
    type: 'bar'
  }

  export interface HeatmapSeriesOption extends BaseSeriesOption {
    type: 'heatmap'
  }
}

declare module 'echarts/components' {
  import {
    TitleComponent,
    TooltipComponent,
    GridComponent,
    DataZoomComponent,
    ToolboxComponent,
    LegendComponent,
    MarkAreaComponent,
    VisualMapComponent
  } from 'echarts/components'
  
  export {
    TitleComponent,
    TooltipComponent,
    GridComponent,
    DataZoomComponent,
    ToolboxComponent,
    LegendComponent,
    MarkAreaComponent,
    VisualMapComponent
  }
  
  export type {
    TitleComponentOption,
    TooltipComponentOption,
    GridComponentOption,
    DataZoomComponentOption,
    ToolboxComponentOption,
    LegendComponentOption,
    MarkAreaComponentOption,
    VisualMapComponentOption
  } from 'echarts/components'
}

declare module 'echarts/renderers' {
  import { CanvasRenderer } from 'echarts/renderers'
  export { CanvasRenderer }
}
