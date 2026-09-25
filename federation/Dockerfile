FROM python:3.11-slim
WORKDIR /fed
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "middleware.py"]