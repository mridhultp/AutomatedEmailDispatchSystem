FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install --no-cache-dir -r Requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]
