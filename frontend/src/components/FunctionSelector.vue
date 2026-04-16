<script setup lang="ts">
const FUNCTIONS = [
  { value: 'weekly_report', label: '周报生成' },
  { value: 'erp_query', label: 'ERP查询' },
  { value: 'shared_query', label: '共享查询' },
]

const model = defineModel<string | null>({ default: null })
</script>

<template>
  <el-select
    v-model="model"
    placeholder="选择功能（可选，AI自动判断）"
    clearable
    style="width: 220px"
    size="default"
  >
    <el-option
      v-for="f in FUNCTIONS"
      :key="f.value"
      :label="f.label"
      :value="f.value"
    />
  </el-select>
</template>
