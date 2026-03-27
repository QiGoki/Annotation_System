# 测试数据说明

本目录包含用于测试标注平台任务管理系统的示例数据。

## 数据文件

### 1. sample_images.jsonl
图像标注测试数据（JSONL 格式），包含 5 条图像记录：
- 使用 picsum.photos 的随机图片 URL
- 适用于图像分类、目标检测、分割等任务

### 2. sample_images.json
图像标注测试数据（JSON 数组格式），包含 8 条图像记录：
- 涵盖动物、车辆、建筑、食物、人物等类别
- 带有 metadata 元数据字段

### 3. sample_texts.jsonl
文本标注测试数据（JSONL 格式），包含 6 条文本记录：
- AI 相关的中文文本
- 适用于文本分类、实体标注等任务

## 数据格式

每条记录应包含 `data_source` 字段：

### 图像类型
```json
{
  "data_source": {
    "type": "image",
    "url": "https://example.com/image.jpg",
    "filename": "image_001.jpg"
  },
  "metadata": {
    "category": "object_detection"
  }
}
```

### 文本类型
```json
{
  "data_source": {
    "type": "text",
    "content": "这是文本内容..."
  },
  "metadata": {
    "language": "zh"
  }
}
```

## 使用方法

### 方法 1：使用 Python 脚本
```bash
cd /home/goki/annotation-platform

# 上传 JSONL 文件
python test_data/upload_test_data.py test_data/sample_images.jsonl

# 上传 JSON 文件
python test_data/upload_test_data.py test_data/sample_images.json
```

### 方法 2：手动上传
1. 访问 http://localhost:5173/projects
2. 选择项目，点击"导入"
3. 选择 JSON 或 JSONL 文件上传

## 注意事项

1. 确保后端服务已启动（http://localhost:8000）
2. 确保已创建至少一个项目
3. 上传的文件格式必须是 .json 或 .jsonl
4. JSONL 文件每行一条完整的 JSON 记录
