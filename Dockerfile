FROM python:3.10-slim

WORKDIR /app

# 安装必要的系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建必要的目录
RUN mkdir -p data config

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["python", "main.py"]
