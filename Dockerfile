FROM python:3.12-slim

WORKDIR /app

# 换国内源，加速 apt
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true
RUN apt-get update && apt-get install -y --no-install-recommends libmagic1 && rm -rf /var/lib/apt/lists/*

# ★ 离线安装：先从本地 wheels 装，失败再走网络
COPY requirements.txt wheels/ /app/
RUN pip install --no-cache-dir --no-index --find-links /app/wheels -r requirements.txt || \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120"]
