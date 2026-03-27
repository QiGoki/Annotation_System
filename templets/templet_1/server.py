import os
import json
import time
import threading
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image

app = Flask(__name__)
CORS(app, supports_credentials=True)

# 配置路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(BASE_DIR, 'resources')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
IMAGES_DIR = '/home/goki/mnt/gui_check/images'

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ========== 文件锁机制 ==========
# 锁结构：{ filename: { 'sessionId': str, 'timestamp': float } }
file_locks = {}
LOCK_TIMEOUT = 90  # 锁超时时间（秒）
LOCK_CHECK_INTERVAL = 30  # 清理超期锁的检查间隔（秒）

def cleanup_expired_locks():
    """后台线程：定期清理超期的锁"""
    while True:
        time.sleep(LOCK_CHECK_INTERVAL)
        current_time = time.time()
        expired_files = []
        for filename, lock_info in file_locks.items():
            if current_time - lock_info['timestamp'] > LOCK_TIMEOUT:
                expired_files.append(filename)
        for filename in expired_files:
            del file_locks[filename]
            print(f"[锁] 文件 '{filename}' 锁已超时，自动释放")

# 启动后台清理线程
cleanup_thread = threading.Thread(target=cleanup_expired_locks, daemon=True)
cleanup_thread.start()


def try_acquire_lock(filename, session_id):
    """
    尝试获取文件锁

    Returns:
        { 'success': bool, 'locked_by': str (可选), 'message': str }
    """
    current_time = time.time()

    if filename in file_locks:
        lock_info = file_locks[filename]
        # 检查是否超时
        if current_time - lock_info['timestamp'] > LOCK_TIMEOUT:
            # 超时，自动释放并重新加锁
            file_locks[filename] = {'sessionId': session_id, 'timestamp': current_time}
            return {'success': True, 'action': 'acquired_expired'}
        # 检查是否是同一个 session（刷新锁）
        if lock_info['sessionId'] == session_id:
            # 刷新锁时间戳
            file_locks[filename]['timestamp'] = current_time
            return {'success': True, 'action': 'refreshed'}
        # 被其他 session 锁定
        return {
            'success': False,
            'locked_by': lock_info['sessionId'],
            'message': f"文件被 session '{lock_info['sessionId']}' 锁定中"
        }

    # 文件未锁定，加锁
    file_locks[filename] = {'sessionId': session_id, 'timestamp': current_time}
    return {'success': True, 'action': 'acquired'}


def release_lock(filename, session_id):
    """释放文件锁"""
    if filename in file_locks:
        lock_info = file_locks[filename]
        if lock_info['sessionId'] == session_id:
            del file_locks[filename]
            return {'success': True, 'message': '锁已释放'}
        else:
            return {'success': False, 'message': '不是锁的持有者，无法释放'}
    return {'success': False, 'message': '文件未被锁定'}


def get_available_jsonl_files():
    """获取所有可用的 JSONL 文件（排除 completed 前缀的文件）"""
    files = []
    if not os.path.exists(RESOURCES_DIR):
        os.makedirs(RESOURCES_DIR)
        return files
    for f in os.listdir(RESOURCES_DIR):
        if f.endswith('.jsonl') and not f.startswith('completed_') and f != 'completed.jsonl':
            files.append(f)
    return sorted(files)


def get_output_file_path(input_file: str) -> str:
    """根据 input 文件名生成 output 文件路径"""
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    return os.path.join(OUTPUT_DIR, f'completed_{base_name}.jsonl')


def load_saved_indices(input_file: str) -> dict:
    """
    从 output 文件加载已保存的数据

    Returns:
        { index: { ...完整数据... }, ... }
    """
    saved_file = get_output_file_path(input_file)
    if not os.path.exists(saved_file):
        return {}

    saved = {}
    with open(saved_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                idx = item.get('_index')
                if idx is not None:
                    saved[idx] = item
    return saved


def load_all_data_with_status(input_file: str, saved_data: dict) -> list:
    """
    加载 JSONL 文件的所有数据，添加 _index 和 _saved 字段，并合并已保存的数据

    Args:
        input_file: 输入文件名
        saved_data: 已保存的数据字典 { index: { ...完整数据... }, ... }
    """
    file_path = os.path.join(RESOURCES_DIR, input_file)
    if not os.path.exists(file_path):
        return []

    items = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for index, line in enumerate(f):
            if line.strip():
                item = json.loads(line)
                item['_index'] = index
                # 如果有已保存的数据，使用已保存的数据内容
                if index in saved_data:
                    # 保留 _index 和 _saved 标记
                    saved_item = saved_data[index].copy()
                    saved_item['_index'] = index
                    saved_item['_saved'] = True
                    items.append(saved_item)
                else:
                    item['_saved'] = False
                    items.append(item)
    return items


@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'annotation_tool_v4.html')


@app.route('/api/files', methods=['GET'])
def get_files():
    """获取所有可用的 JSONL 文件列表及完成状态"""
    files = get_available_jsonl_files()
    file_status = []

    for f in files:
        saved_data = load_saved_indices(f)
        saved_count = len(saved_data)

        # 计算总数
        file_path = os.path.join(RESOURCES_DIR, f)
        total = 0
        with open(file_path, 'r', encoding='utf-8') as fp:
            for line in fp:
                if line.strip():
                    total += 1

        # 检查文件锁状态
        locked = f in file_locks
        locked_by = file_locks[f]['sessionId'] if locked else None

        file_status.append({
            'filename': f,
            'total': total,
            'completed': saved_count,
            'remaining': total - saved_count,
            'locked': locked,
            'locked_by': locked_by
        })

    return jsonify({'files': file_status})


@app.route('/api/lock', methods=['POST'])
def api_lock():
    """获取文件锁"""
    # 尝试从 JSON body 获取参数
    try:
        data = request.get_json(force=True) or {}
    except:
        data = {}

    filename = data.get('filename')
    session_id = data.get('sessionId')

    if not filename:
        return jsonify({
            'success': False,
            'message': '缺少 filename 参数'
        }), 400

    if not session_id:
        return jsonify({
            'success': False,
            'message': '缺少 sessionId 参数'
        }), 400

    result = try_acquire_lock(filename, session_id)
    return jsonify(result)


@app.route('/api/unlock', methods=['POST'])
def api_unlock():
    """释放文件锁"""
    try:
        data = request.get_json(force=True) or {}
    except:
        data = {}

    filename = data.get('filename')
    session_id = data.get('sessionId')

    if not filename or not session_id:
        return jsonify({
            'success': False,
            'message': '缺少 filename 或 sessionId 参数'
        }), 400

    result = release_lock(filename, session_id)
    return jsonify(result)


@app.route('/api/heartbeat', methods=['POST'])
def api_heartbeat():
    """心跳，刷新锁的时间戳"""
    try:
        data = request.get_json(force=True) or {}
    except:
        data = {}

    filename = data.get('filename')
    session_id = data.get('sessionId')

    if not filename or not session_id:
        return jsonify({
            'success': False,
            'message': '缺少 filename 或 sessionId 参数'
        }), 400

    if filename in file_locks and file_locks[filename]['sessionId'] == session_id:
        file_locks[filename]['timestamp'] = time.time()
        return jsonify({'success': True, 'message': '心跳已接收'})
    else:
        return jsonify({
            'success': False,
            'message': '文件未被此 session 锁定'
        }), 404


@app.route('/api/data', methods=['GET'])
def get_data():
    """获取所有数据（包含 _saved 状态）"""
    filename = request.args.get('filename')

    if not filename:
        return jsonify({
            'error': '请指定 filename 参数',
            'files': get_available_jsonl_files()
        }), 400

    # 从 output 文件加载已保存的数据
    saved_data = load_saved_indices(filename)
    saved_indices = set(saved_data.keys())

    # 加载数据（包含已保存的数据内容）
    all_data = load_all_data_with_status(filename, saved_data)

    return jsonify({
        'items': all_data,
        'total': len(all_data),
        'completed': len(saved_indices),
        'remaining': len(all_data) - len(saved_indices),
        'current_file': filename
    })


@app.route('/api/save', methods=['POST'])
def save_item():
    """保存单条数据"""
    filename = request.args.get('filename')

    if not filename:
        return jsonify({'success': False, 'error': '请指定 filename 参数'})

    try:
        data = request.json
        data_index = data.get('_index')

        if data_index is None:
            return jsonify({'success': False, 'error': '缺少 _index'})

        # 强制设置 _saved 为 true，表示这条数据已经保存过
        data['_saved'] = True

        # 获取 output 文件路径
        output_file = get_output_file_path(filename)

        # 读取现有数据
        existing = []
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        existing.append(json.loads(line))

        # 查找并更新或追加
        found = False
        for i, item in enumerate(existing):
            if item.get('_index') == data_index:
                existing[i] = data
                found = True
                break

        if not found:
            existing.append(data)

        # 写回文件
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in existing:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        return jsonify({'success': True, 'action': 'saved'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/status', methods=['GET'])
def get_status():
    """获取当前文件的完成状态统计"""
    filename = request.args.get('filename')

    if not filename:
        return jsonify({'total': 0, 'completed': 0, 'remaining': 0, 'saved_indices': []})

    # 从 output 文件加载已保存的索引
    saved_data = load_saved_indices(filename)
    saved_indices = set(saved_data.keys())

    # 计算总数
    file_path = os.path.join(RESOURCES_DIR, filename)
    total = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                total += 1

    return jsonify({
        'total': total,
        'completed': len(saved_indices),
        'remaining': total - len(saved_indices),
        'saved_indices': list(saved_indices)
    })


@app.route('/api/submit', methods=['POST'])
def submit_file():
    """提交文件：检查是否全部完成"""
    filename = request.args.get('filename')

    if not filename:
        return jsonify({'success': False, 'error': '请指定 filename 参数'})

    # 从 output 文件加载已保存的索引
    saved_data = load_saved_indices(filename)
    saved_indices = set(saved_data.keys())

    # 计算总数
    file_path = os.path.join(RESOURCES_DIR, filename)
    total = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                total += 1

    if len(saved_indices) < total:
        return jsonify({
            'success': False,
            'error': f'还有 {total - len(saved_indices)} 条未完成',
            'completed': len(saved_indices),
            'total': total
        })

    return jsonify({'success': True, 'message': '已全部完成，文件已保存到 output 目录'})


@app.route('/api/images/<path:filename>')
def serve_image(filename):
    """提供图片服务"""
    image_path = os.path.join(IMAGES_DIR, filename)

    if not os.path.exists(image_path):
        return jsonify({'error': '图片不存在：' + filename}), 404

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


if __name__ == '__main__':
    print(f"服务启动：http://localhost:4998")
    print(f"图片目录：{IMAGES_DIR}")
    print(f"可用的 JSONL 文件：{get_available_jsonl_files()}")
    app.run(host='0.0.0.0', port=4998, debug=True)
