<template>
  <div class="clothing-card">
    <div class="card-header">
      <el-icon><Suitcase /></el-icon>
      <h3>穿搭建议</h3>
    </div>

    <div class="card-body">
      <!-- 天气信息 -->
      <div class="weather-info">
        <el-icon><Sunny /></el-icon>
        <span>{{ advice.weather_summary }} | {{ advice.temperature }}°C</span>
      </div>

      <!-- 场合和风格 -->
      <div class="occasion-style">
        <el-tag type="primary">{{ advice.occasion }}</el-tag>
        <el-tag type="success">{{ advice.style }}</el-tag>
      </div>

      <!-- 穿搭列表 -->
      <div class="clothing-items">
        <div v-if="advice.tops && advice.tops.length > 0" class="item-group">
          <h4>上衣</h4>
          <div v-for="item in advice.tops" :key="item.name" class="clothing-item">
            <span class="item-name">{{ item.name }}</span>
            <span class="item-color">{{ item.color }}</span>
            <span v-if="item.material" class="item-material">{{ item.material }}</span>
          </div>
        </div>

        <div v-if="advice.bottoms && advice.bottoms.length > 0" class="item-group">
          <h4>下装</h4>
          <div v-for="item in advice.bottoms" :key="item.name" class="clothing-item">
            <span class="item-name">{{ item.name }}</span>
            <span class="item-color">{{ item.color }}</span>
            <span v-if="item.material" class="item-material">{{ item.material }}</span>
          </div>
        </div>

        <div v-if="advice.outerwear && advice.outerwear.length > 0" class="item-group">
          <h4>外套</h4>
          <div v-for="item in advice.outerwear" :key="item.name" class="clothing-item">
            <span class="item-name">{{ item.name }}</span>
            <span class="item-color">{{ item.color }}</span>
            <span v-if="item.material" class="item-material">{{ item.material }}</span>
          </div>
        </div>

        <div v-if="advice.shoes && advice.shoes.length > 0" class="item-group">
          <h4>鞋子</h4>
          <div v-for="item in advice.shoes" :key="item.name" class="clothing-item">
            <span class="item-name">{{ item.name }}</span>
            <span class="item-color">{{ item.color }}</span>
          </div>
        </div>

        <div v-if="advice.accessories && advice.accessories.length > 0" class="item-group">
          <h4>配饰</h4>
          <div v-for="item in advice.accessories" :key="item.name" class="clothing-item">
            <span class="item-name">{{ item.name }}</span>
            <span class="item-color">{{ item.color }}</span>
          </div>
        </div>
      </div>

      <!-- 推荐理由 -->
      <div class="reason">
        <h4>推荐理由</h4>
        <p>{{ advice.reason }}</p>
      </div>

      <!-- 色系说明 -->
      <div v-if="advice.color_scheme" class="color-scheme">
        <h4>色系搭配</h4>
        <p>{{ advice.color_scheme }}</p>
      </div>

      <!-- 温馨提示 -->
      <div v-if="advice.tips" class="tips">
        <el-icon><InfoFilled /></el-icon>
        <span>{{ advice.tips }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue'
import type { ClothingAdvice } from '@/types/chat'
import { Sunny, InfoFilled, Suitcase } from '@element-plus/icons-vue'

defineProps({
  advice: {
    type: Object as PropType<ClothingAdvice>,
    required: true
  }
})
</script>

<style scoped>
.clothing-card {
  margin-top: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  overflow: hidden;
  background-color: #f9fafb;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background-color: #409eff;
  color: white;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
}

.card-body {
  padding: 16px;
}

.weather-info {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #606266;
  margin-bottom: 12px;
}

.occasion-style {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.item-group {
  margin-bottom: 12px;
}

.item-group h4 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 14px;
}

.clothing-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px dashed #e4e7ed;
}

.item-name {
  font-weight: 500;
  color: #303133;
}

.item-color {
  color: #409eff;
  font-size: 13px;
}

.item-material {
  color: #909399;
  font-size: 12px;
}

.reason, .color-scheme {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #e4e7ed;
}

.reason h4, .color-scheme h4 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 14px;
}

.reason p, .color-scheme p {
  margin: 0;
  color: #606266;
  line-height: 1.6;
}

.tips {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 12px;
  padding: 10px;
  background-color: #f0f9ff;
  border-radius: 6px;
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
}

.tips .el-icon {
  color: #409eff;
  margin-top: 2px;
  flex-shrink: 0;
}
</style>
