FROM python:3.10.20

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --progress-bar off -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制代码
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio", "--http", "h11"]
