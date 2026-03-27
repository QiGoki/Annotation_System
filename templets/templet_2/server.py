import os
import json
from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
from PIL import Image

from annotation_session import (
    SessionManager,
    FileLockManager,
    init_session_from_request,
    save_session_to_cookie,
)

app = Flask(__name__)
CORS(app, supports_credentials=True)

# 配置路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(BASE_DIR, 'resources')
IMAGES_DIR = '/home/goki/mnt/adonly_allbboxes_with_chat/images'


def get_status_file_path(input_file: str) -> str:
    """根据输入文件名生成状态缓存文件路径"""
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    return os.path.join(RESOURCES_DIR, f'.{base_name}.status.jsonl')


def load_status_data(input_file: str) -> dict:
    """
    从状态缓存文件加载已完成的数据

    Returns:
        { index: is_completed, ... }
    """
    status_file = get_status_file_path(input_file)
    if not os.path.exists(status_file):
        return {}

    status = {}
    with open(status_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                idx = item.get('index')
                is_completed = item.get('is_completed', False)
                if idx is not None:
                    status[idx] = is_completed
    return status


def save_status_data(input_file: str, index: int, is_completed: bool, data: dict = None) -> None:
    """
    保存单条数据的状态到缓存文件，并更新原文件

    Args:
        input_file: 原文件名
        index: 行号索引
        is_completed: 完成状态
        data: 要保存的完整数据（如果为 None，只更新状态）
    """
    status_file = get_status_file_path(input_file)
    file_path = os.path.join(RESOURCES_DIR, input_file)

    # 1. 更新状态缓存文件
    status = load_status_data(input_file)
    status[index] = is_completed

    # 写回状态文件
    with open(status_file, 'w', encoding='utf-8') as f:
        for idx, completed in status.items():
            f.write(json.dumps({'index': idx, 'is_completed': completed}, ensure_ascii=False) + '\n')

    # 2. 如果需要更新原文件数据
    if data is not None and os.path.exists(file_path):
        # 读取原文件所有行
        items = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    items.append(json.loads(line))

        # 更新对应索引的数据
        if index < len(items):
            items[index] = data
            # 写回原文件
            with open(file_path, 'w', encoding='utf-8') as f:
                for item in items:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')

# 初始化 Session 和锁管理器
session_manager = SessionManager(secret_key='check-bbox-with-answer-secret-2026', timeout_minutes=60)
file_lock_manager = FileLockManager()


def get_available_jsonl_files():
    """获取所有可用的 JSONL 文件（排除隐藏文件和状态文件）"""
    files = []
    if not os.path.exists(RESOURCES_DIR):
        os.makedirs(RESOURCES_DIR)
        return files
    for f in os.listdir(RESOURCES_DIR):
        # 排除隐藏文件和状态文件
        if f.endswith('.jsonl') and not f.startswith('.'):
            files.append(f)
    return sorted(files)


def load_all_data(input_file: str) -> list:
    """加载 JSONL 文件的所有数据"""
    file_path = os.path.join(RESOURCES_DIR, input_file)
    if not os.path.exists(file_path):
        return []
    items = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items


@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'annotation_tool_v2.html')


@app.route('/api/files', methods=['GET'])
def get_files():
    """获取所有可用的 JSONL 文件列表"""
    files = get_available_jsonl_files()
    file_status = []
    for f in files:
        status_data = load_status_data(f)
        completed_count = sum(1 for v in status_data.values() if v)
        total_count = len(load_all_data(f))
        file_status.append({
            'filename': f,
            'total': total_count,
            'completed': completed_count,
            'remaining': total_count - completed_count
        })
    return jsonify({'files': file_status})


@app.route('/api/select_file', methods=['POST'])
def select_file():
    """选择当前要标注的文件"""
    session_id = init_session_from_request(session_manager, request)
    data = request.json
    filename = data.get('filename')

    if not filename:
        return jsonify({'success': False, 'error': '未指定文件名'})

    file_path = os.path.join(RESOURCES_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': '文件不存在'})

    # 从状态缓存文件加载已完成的索引
    status_data = load_status_data(filename)
    completed_indices = set(idx for idx, completed in status_data.items() if completed)

    # 更新 Session
    session_manager.set(session_id, 'current_input_file', filename)
    session_manager.set(session_id, 'completed_indices', list(completed_indices))

    response = make_response(jsonify({'success': True, 'filename': filename}))
    save_session_to_cookie(session_id, response)
    return response


@app.route('/api/data', methods=['GET'])
def get_data():
    """获取完整数据列表（包含 is_completed 标记）"""
    session_id = init_session_from_request(session_manager, request)

    input_file = session_manager.get(session_id, 'current_input_file')
    if not input_file:
        return jsonify({
            'error': '请先选择要标注的文件',
            'files': get_available_jsonl_files()
        }), 400

    # 从缓存文件加载状态
    status_data = load_status_data(input_file)
    all_data = load_all_data(input_file)

    # 给每条数据添加 index 和 is_completed 标记
    items = []
    for idx, item in enumerate(all_data):
        item_copy = {**item, 'index': idx, 'is_completed': status_data.get(idx, False)}
        items.append(item_copy)

    # 找到下一个未完成的索引（用于前端跳转）
    next_incomplete_index = None
    for idx, item in enumerate(items):
        if not item['is_completed']:
            next_incomplete_index = idx
            break

    completed_count = sum(1 for v in status_data.values() if v)

    return jsonify({
        'items': items,
        'total': len(all_data),
        'completed': completed_count,
        'remaining': len(all_data) - completed_count,
        'next_incomplete_index': next_incomplete_index,
        'current_file': input_file
    })


@app.route('/api/save', methods=['POST'])
def save_item():
    """保存单个数据，更新原文件并标记 is_completed=true"""
    session_id = init_session_from_request(session_manager, request)

    input_file = session_manager.get(session_id, 'current_input_file')
    if not input_file:
        return jsonify({'success': False, 'error': '未选择文件'})

    try:
        data = request.json
        data_index = data.get('index')

        if data_index is None:
            return jsonify({'success': False, 'error': '缺少 index 参数'})

        # 使用文件锁保护写入操作
        with file_lock_manager.acquire(input_file, timeout=30.0) as acquired:
            if not acquired:
                return jsonify({
                    'success': False,
                    'error': '文件被占用，请稍后重试'
                })

            # 保存数据并更新状态
            save_status_data(input_file, data_index, True, data)

            # 更新 session 中的完成状态
            completed_indices = session_manager.get(session_id, 'completed_indices', [])
            if data_index not in completed_indices:
                completed_indices.append(data_index)
                session_manager.set(session_id, 'completed_indices', completed_indices)

        return jsonify({
            'success': True,
            'action': 'saved',
            'index': data_index
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/current_file', methods=['GET'])
def get_current_file():
    """获取当前选择的文件信息"""
    session_id = init_session_from_request(session_manager, request)

    input_file = session_manager.get(session_id, 'current_input_file')
    if not input_file:
        return jsonify({'selected': None, 'files': get_available_jsonl_files()})

    status_data = load_status_data(input_file)
    completed_count = sum(1 for v in status_data.values() if v)
    all_data = load_all_data(input_file)

    return jsonify({
        'selected': input_file,
        'total': len(all_data),
        'completed': completed_count,
        'remaining': len(all_data) - completed_count,
        'files': get_available_jsonl_files()
    })


@app.route('/api/images/<path:filename>')
def serve_image(filename):
    """提供图片服务"""
    if filename.startswith('images/'):
        filename = filename[7:]
    return send_from_directory(IMAGES_DIR, filename)


@app.route('/api/image/info', methods=['GET'])
def get_image_info():
    """获取图片分辨率信息"""
    filename = request.args.get('filename', '')
    if not filename:
        return jsonify({'error': '缺少 filename 参数'}), 400

    if filename.startswith('images/'):
        filename = filename[7:]

    image_path = os.path.join(IMAGES_DIR, filename)

    if not os.path.exists(image_path):
        return jsonify({'error': '图片不存在'}), 404

    try:
        with Image.open(image_path) as img:
            return jsonify({
                'width': img.width,
                'height': img.height,
                'filename': filename
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/debug/sessions', methods=['GET'])
def debug_sessions():
    """调试接口：查看所有活跃 Session"""
    return jsonify({
        'sessions': session_manager.get_all_sessions_info()
    })


if __name__ == '__main__':
    print(f"服务启动：http://localhost:4996")
    print(f"图片目录：{IMAGES_DIR}")
    print(f"可用的 JSONL 文件：{get_available_jsonl_files()}")
    app.run(host='0.0.0.0', port=4996, debug=True)
