FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 依赖安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝后端代码
COPY . /app

# 默认配置，Zeabur 可通过环境变量覆盖 DATABASE_URL/SECRET_KEY 等
ENV FLASK_ENV=production \
    PORT=8000

EXPOSE 8000

# 运行 Flask 应用
CMD ["python", "run.py"]
