# 开发环境启动脚本
# 使用方法：source scripts/dev.sh

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
