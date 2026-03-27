FROM python:3.10.20

WORKDIR /app

# 设置大文件上传环境变量（python-multipart 0.0.6 会读取）
ENV MULTIPART_MAX_MEMORY_SIZE=524288000
ENV MULTIPART_MAX_FILE_SIZE=524288000

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --progress-bar off -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制代码
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio", "--http", "h11", "--timeout-keep-alive", "120"]
