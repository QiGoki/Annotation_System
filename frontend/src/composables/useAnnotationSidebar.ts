/**
 * 标注侧边栏状态管理 Composable
 */
import { ref, computed, reactive } from 'vue'

export interface TaskData {
  id?: number
  filename?: string
  _saved?: boolean
  [key: string]: any
}

export interface SidebarStats {
  total: number
  completed: number
  remaining: number
}

export interface ListItem {
  index: number
  filename?: string
  saved?: boolean
}

/**
 * 使用标注侧边栏状态管理
 * @param taskData 任务数据数组
 */
export function useAnnotationSidebar(taskData: TaskData[]) {
  // 当前选中的索引
  const currentIndex = ref(0)

  // 已保存的索引集合
  const savedIndices = reactive(new Set<number>())

  // 统计数据
  const stats = computed<SidebarStats>(() => {
    const total = taskData.length
    const completed = savedIndices.size
    return {
      total,
      completed,
      remaining: total - completed
    }
  })

  // 已完成条目
  const completedItems = computed<ListItem[]>(() => {
    return taskData
      .map((item, index) => ({
        index,
        filename: item.filename || item.image || `Item ${index + 1}`,
        saved: item._saved
      }))
      .filter(item => item.saved)
  })

  // 未完成条目
  const remainingItems = computed<ListItem[]>(() => {
    return taskData
      .map((item, index) => ({
        index,
        filename: item.filename || item.image || `Item ${index + 1}`,
        saved: item._saved
      }))
      .filter(item => !item.saved)
  })

  /**
   * 选择条目
   */
  const selectItem = (index: number) => {
    if (index >= 0 && index < taskData.length) {
      currentIndex.value = index
    }
  }

  /**
   * 标记为已保存
   */
  const markAsSaved = (index: number) => {
    savedIndices.add(index)
    if (taskData[index]) {
      taskData[index]._saved = true
    }
  }

  /**
   * 标记为未保存
   */
  const markAsUnsaved = (index: number) => {
    savedIndices.delete(index)
    if (taskData[index]) {
      taskData[index]._saved = false
    }
  }

  /**
   * 检查是否已保存
   */
  const isSaved = (index: number): boolean => {
    return savedIndices.has(index)
  }

  /**
   * 获取当前条目
   */
  const currentItem = computed<TaskData | null>(() => {
    if (currentIndex.value >= 0 && currentIndex.value < taskData.length) {
      return taskData[currentIndex.value]
    }
    return null
  })

  /**
   * 上一条
   */
  const previousItem = () => {
    if (currentIndex.value > 0) {
      currentIndex.value--
    }
  }

  /**
   * 下一条（跳过已完成的）
   */
  const nextItem = () => {
    // 找下一条未完成的
    for (let i = currentIndex.value + 1; i < taskData.length; i++) {
      if (!savedIndices.has(i)) {
        currentIndex.value = i
        return
      }
    }
  }

  /**
   * 重置状态（切换任务时使用）
   */
  const reset = () => {
    currentIndex.value = 0
    savedIndices.clear()
  }

  return {
    // 状态
    currentIndex,
    stats,
    completedItems,
    remainingItems,
    savedIndices,
    currentItem,

    // 方法
    selectItem,
    markAsSaved,
    markAsUnsaved,
    isSaved,
    previousItem,
    nextItem,
    reset
  }
}
