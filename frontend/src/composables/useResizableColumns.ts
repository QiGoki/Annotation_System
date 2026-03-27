/**
 * 可调整列宽的 Composable
 * 用于实现鼠标拖拽调整列宽的功能
 */
import { ref, onMounted, onUnmounted } from 'vue'

export interface ColumnWidth {
  index: number
  width: number  // 像素值
  percent: number  // 百分比
}

export function useResizableColumns(
  containerRef: HTMLElement | null,
  initialWidths: number[] = [25, 45, 30],  // 默认百分比 25%, 45%, 30%
  minPercent: number = 10,  // 最小宽度百分比
  maxPercent: number = 60   // 最大宽度百分比
) {
  // 列宽数据（百分比）
  const columnPercents = ref<number[]>([...initialWidths])

  // 拖拽状态
  const isResizing = ref(false)
  const resizingColumnIndex = ref(-1)  // 正在调整的是哪一列的右侧边界（0 表示第 1 列右侧，1 表示第 2 列右侧）
  const startX = ref(0)
  const startWidths = ref<number[]>([])

  // 获取列的像素宽度
  const getColumnWidthsInPixels = (containerWidth: number): number[] => {
    return columnPercents.value.map(percent => (percent / 100) * containerWidth)
  }

  // 开始调整
  const startResize = (event: MouseEvent, columnIndex: number) => {
    if (!containerRef) return

    isResizing.value = true
    resizingColumnIndex.value = columnIndex
    startX.value = event.clientX

    // 保存当前宽度
    startWidths.value = [...columnPercents.value]

    // 添加全局事件监听
    document.addEventListener('mousemove', handleResize)
    document.addEventListener('mouseup', stopResize)

    // 防止选中文字
    event.preventDefault()
    event.stopPropagation()
  }

  // 调整中
  const handleResize = (event: MouseEvent) => {
    if (!isResizing.value || !containerRef) return

    const deltaX = event.clientX - startX.value
    const containerWidth = containerRef.offsetWidth

    // 计算百分比变化
    const deltaPercent = (deltaX / containerWidth) * 100

    const leftColIndex = resizingColumnIndex.value
    const rightColIndex = resizingColumnIndex.value + 1

    if (rightColIndex >= columnPercents.value.length) return

    // 计算新宽度
    let newLeftPercent = startWidths.value[leftColIndex] + deltaPercent
    let newRightPercent = startWidths.value[rightColIndex] - deltaPercent

    // 应用最小/最大限制
    const leftMin = Math.max(minPercent, 100 - columnPercents.value.reduce((sum, p, i) => i !== leftColIndex ? sum + p : sum))
    const leftMax = Math.min(maxPercent, 100 - columnPercents.value.reduce((sum, p, i) => i !== leftColIndex && i !== rightColIndex ? sum + p : sum) - minPercent)

    newLeftPercent = Math.max(leftMin, Math.min(leftMax, newLeftPercent))
    newRightPercent = 100 - columnPercents.value.reduce((sum, p, i) => {
      if (i === leftColIndex) return sum + newLeftPercent
      if (i !== rightColIndex) return sum + p
      return sum
    }, 0)

    // 更新宽度
    columnPercents.value[leftColIndex] = newLeftPercent
    columnPercents.value[rightColIndex] = newRightPercent
  }

  // 停止调整
  const stopResize = () => {
    isResizing.value = false
    resizingColumnIndex.value = -1

    // 移除全局事件监听
    document.removeEventListener('mousemove', handleResize)
    document.removeEventListener('mouseup', stopResize)
  }

  // 重置为默认宽度
  const resetWidths = () => {
    columnPercents.value = [...initialWidths]
  }

  // 设置特定列的宽度
  const setColumnWidth = (index: number, percent: number) => {
    if (index < 0 || index >= columnPercents.value.length) return
    columnPercents.value[index] = Math.max(minPercent, Math.min(maxPercent, percent))
  }

  // 获取列宽样式
  const getColumnStyle = (index: number) => {
    return {
      width: `${columnPercents.value[index]}%`,
      flex: `0 0 ${columnPercents.value[index]}%`
    }
  }

  // 判断是否显示调整光标
  const getCursorStyle = (columnIndex: number, isHovered: boolean) => {
    if (!isHovered) return 'default'
    if (columnIndex >= columnPercents.value.length - 1) return 'default'
    return 'col-resize'
  }

  return {
    columnPercents,
    isResizing,
    startResize,
    resetWidths,
    setColumnWidth,
    getColumnStyle,
    getCursorStyle,
    getColumnWidthsInPixels
  }
}
