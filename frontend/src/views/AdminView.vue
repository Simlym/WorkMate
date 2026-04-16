<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminApi, type AdminUser, type UserCreate } from '@/api/admin'
import {
  datasourcesApi,
  type Datasource,
  type DatasourceCreate,
  DATASOURCE_TYPES,
} from '@/api/datasources'
import { useAuthStore } from '@/stores/auth'
import request from '@/api/request'

const auth = useAuthStore()
const activeTab = ref('users')

// ─── Users ─────────────────────────────────────────────────────────────────
const users = ref<AdminUser[]>([])
const userLoading = ref(false)
const showUserDialog = ref(false)
const userForm = ref<UserCreate>({ employee_id: '', display_name: '', password: '', is_admin: false })

async function fetchUsers() {
  userLoading.value = true
  try {
    users.value = (await adminApi.listUsers()).data
  } finally {
    userLoading.value = false
  }
}

async function submitUser() {
  try {
    await adminApi.createUser(userForm.value)
    ElMessage.success('用户已创建')
    showUserDialog.value = false
    userForm.value = { employee_id: '', display_name: '', password: '', is_admin: false }
    fetchUsers()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '创建失败')
  }
}

async function toggleUserActive(user: AdminUser) {
  await adminApi.updateUser(user.id, { is_active: !user.is_active })
  user.is_active = !user.is_active
}

async function deleteUser(user: AdminUser) {
  await ElMessageBox.confirm(`确认删除用户 ${user.employee_id}？`, '删除确认', { type: 'warning' })
  await adminApi.deleteUser(user.id)
  ElMessage.success('已删除')
  fetchUsers()
}

// ─── Skills ────────────────────────────────────────────────────────────────
const skills = ref<any[]>([])
const skillLoading = ref(false)
const uploadRef = ref()

async function fetchSkills() {
  skillLoading.value = true
  try {
    skills.value = (await request.get('/skills')).data
  } finally {
    skillLoading.value = false
  }
}

async function uploadSkill(file: File) {
  const fd = new FormData()
  fd.append('file', file)
  try {
    await request.post('/skills', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    ElMessage.success('Skill 安装成功')
    fetchSkills()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '安装失败')
  }
  return false // prevent default upload
}

async function toggleSkill(skill: any) {
  const endpoint = skill.enabled ? `/skills/${skill.id}/disable` : `/skills/${skill.id}/enable`
  await request.patch(endpoint)
  skill.enabled = !skill.enabled
}

async function deleteSkill(skill: any) {
  await ElMessageBox.confirm(`确认卸载 Skill「${skill.name}」？`, '确认', { type: 'warning' })
  await request.delete(`/skills/${skill.id}`)
  ElMessage.success('已卸载')
  fetchSkills()
}

// ─── Datasources ───────────────────────────────────────────────────────────
const datasources = ref<Datasource[]>([])
const dsLoading = ref(false)
const showDsDialog = ref(false)
const editingDs = ref<Datasource | null>(null)
const dsForm = ref<DatasourceCreate>({ name: '', type: 'mysql', description: '', config: {}, enabled: true })
const dsConfigStr = ref('{}')

async function fetchDatasources() {
  dsLoading.value = true
  try {
    datasources.value = (await datasourcesApi.list()).data
  } finally {
    dsLoading.value = false
  }
}

function openDsDialog(ds?: Datasource) {
  if (ds) {
    editingDs.value = ds
    dsForm.value = { name: ds.name, type: ds.type, description: ds.description, config: ds.config, enabled: ds.enabled }
    dsConfigStr.value = JSON.stringify(ds.config, null, 2)
  } else {
    editingDs.value = null
    dsForm.value = { name: '', type: 'mysql', description: '', config: {}, enabled: true }
    dsConfigStr.value = '{}'
  }
  showDsDialog.value = true
}

async function submitDs() {
  try {
    dsForm.value.config = JSON.parse(dsConfigStr.value)
  } catch {
    ElMessage.error('Config 不是合法的 JSON')
    return
  }
  try {
    if (editingDs.value) {
      await datasourcesApi.update(editingDs.value.id, dsForm.value)
      ElMessage.success('已更新')
    } else {
      await datasourcesApi.create(dsForm.value)
      ElMessage.success('已添加')
    }
    showDsDialog.value = false
    fetchDatasources()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  }
}

async function testDs(ds: Datasource) {
  const res = await datasourcesApi.test(ds.id)
  if (res.data.success) {
    ElMessage.success(res.data.message)
  } else {
    ElMessage.error(res.data.message)
  }
}

async function deleteDs(ds: Datasource) {
  await ElMessageBox.confirm(`确认删除数据源「${ds.name}」？`, '确认', { type: 'warning' })
  await datasourcesApi.delete(ds.id)
  ElMessage.success('已删除')
  fetchDatasources()
}

onMounted(() => {
  fetchUsers()
  fetchSkills()
  fetchDatasources()
})
</script>

<template>
  <div class="admin-view">
    <div class="admin-header">
      <h2>系统管理</h2>
      <el-button text @click="$router.push('/')">← 返回对话</el-button>
    </div>

    <el-tabs v-model="activeTab" class="admin-tabs">
      <!-- ── Users ── -->
      <el-tab-pane label="用户管理" name="users">
        <div class="tab-toolbar">
          <el-button type="primary" @click="showUserDialog = true">新建用户</el-button>
        </div>
        <el-table :data="users" v-loading="userLoading" stripe>
          <el-table-column prop="employee_id" label="工号" width="160" />
          <el-table-column prop="display_name" label="姓名" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="管理员" width="90">
            <template #default="{ row }">
              <el-tag v-if="row.is_admin" type="warning" size="small">管理员</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="170">
            <template #default="{ row }">{{ row.created_at.slice(0, 19).replace('T', ' ') }}</template>
          </el-table-column>
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button size="small" text @click="toggleUserActive(row)">
                {{ row.is_active ? '禁用' : '启用' }}
              </el-button>
              <el-button size="small" text type="danger" @click="deleteUser(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ── Skills ── -->
      <el-tab-pane label="Skills 管理" name="skills">
        <div class="tab-toolbar">
          <el-upload :before-upload="uploadSkill" accept=".zip" :show-file-list="false">
            <el-button type="primary">上传 Skill (.zip)</el-button>
          </el-upload>
        </div>
        <el-table :data="skills" v-loading="skillLoading" stripe>
          <el-table-column prop="name" label="名称" width="160" />
          <el-table-column prop="version" label="版本" width="90" />
          <el-table-column prop="description" label="描述" />
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
                {{ row.enabled ? '运行中' : '已停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="installed_at" label="安装时间" width="170">
            <template #default="{ row }">{{ row.installed_at.slice(0, 19).replace('T', ' ') }}</template>
          </el-table-column>
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button size="small" text @click="toggleSkill(row)">
                {{ row.enabled ? '停用' : '启用' }}
              </el-button>
              <el-button size="small" text type="danger" @click="deleteSkill(row)">卸载</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ── Datasources ── -->
      <el-tab-pane label="数据源配置" name="datasources">
        <div class="tab-toolbar">
          <el-button type="primary" @click="openDsDialog()">新增数据源</el-button>
        </div>
        <el-table :data="datasources" v-loading="dsLoading" stripe>
          <el-table-column prop="name" label="名称" width="160" />
          <el-table-column prop="type" label="类型" width="120" />
          <el-table-column prop="description" label="描述" />
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
                {{ row.enabled ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200">
            <template #default="{ row }">
              <el-button size="small" text @click="testDs(row)">测试连接</el-button>
              <el-button size="small" text @click="openDsDialog(row)">编辑</el-button>
              <el-button size="small" text type="danger" @click="deleteDs(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- ── New User Dialog ── -->
    <el-dialog v-model="showUserDialog" title="新建用户" width="440px">
      <el-form :model="userForm" label-width="80px">
        <el-form-item label="工号">
          <el-input v-model="userForm.employee_id" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="userForm.display_name" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="userForm.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="管理员">
          <el-switch v-model="userForm.is_admin" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUserDialog = false">取消</el-button>
        <el-button type="primary" @click="submitUser">创建</el-button>
      </template>
    </el-dialog>

    <!-- ── Datasource Dialog ── -->
    <el-dialog v-model="showDsDialog" :title="editingDs ? '编辑数据源' : '新增数据源'" width="560px">
      <el-form :model="dsForm" label-width="90px">
        <el-form-item label="名称">
          <el-input v-model="dsForm.name" :disabled="!!editingDs" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="dsForm.type" :disabled="!!editingDs">
            <el-option v-for="t in DATASOURCE_TYPES" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="dsForm.description" />
        </el-form-item>
        <el-form-item label="配置 (JSON)">
          <el-input
            v-model="dsConfigStr"
            type="textarea"
            :rows="6"
            placeholder='{"host":"localhost","port":3306,"username":"root","password":"","database":"mydb"}'
          />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="dsForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDsDialog = false">取消</el-button>
        <el-button type="primary" @click="submitDs">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.admin-view {
  min-height: 100vh;
  padding: 24px 32px;
  background: #f5f7fa;
}
.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.admin-header h2 {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
}
.admin-tabs {
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
}
.tab-toolbar {
  margin-bottom: 14px;
}
</style>
