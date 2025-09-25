# 使用官方Python鏡像作為基礎鏡像
FROM python:3.11-slim

# 設置工作目錄
WORKDIR /app

# 更新系統包並安裝依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製API服務的requirements.txt文件到工作目錄
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Diagnostic commands for psycopg2
RUN pip show psycopg2-binary
RUN python -c "import psycopg2; print(psycopg2.__file__)"
RUN python -c "import sys; print(sys.path)"

# 複製應用程序代碼到工作目錄
COPY api/app/ app/
COPY api/web/ web/

# 創建環境變量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app:${PATH}"

# 暴露端口（同時暴露API和Web服務的端口）
EXPOSE 8000 7860

# 默認啓動命令 - API服務
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
