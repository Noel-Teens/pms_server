# Base Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

RUN chmod -R 777 /app

# Expose port
EXPOSE 7860

# Run the Django app using Uvicorn
CMD ["python", "app.py"]
# CMD ["uvicorn", "job_scraper_server.asgi:application", "--host", "0.0.0.0", "--port", "7860"]
