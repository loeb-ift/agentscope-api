# 使用官方Python镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 更新系统包并安装依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制API服务的requirements.txt文件到工作目录
COPY requirements.txt .

# 复制Web服务的requirements.txt文件到工作目录
COPY web/requirements.txt web-requirements.txt

# 安装Python依赖（先安装API依赖，再安装Web依赖）
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r web-requirements.txt

# 复制应用程序代码到工作目录
COPY app/ app/
COPY web/ web/

# 创建环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app:${PATH}"

# 暴露端口（同时暴露API和Web服务的端口）
EXPOSE 8000 7860

# 默认启动命令 - API服务
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]