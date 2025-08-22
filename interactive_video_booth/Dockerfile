# Optional Dockerfile (use if running containerized)
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Expose WS server
EXPOSE 8765
# For Flask control UI if enabled
EXPOSE 8080
CMD ["python", "-m", "app.main"]
