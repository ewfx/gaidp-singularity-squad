# Production stage
FROM python:3.11-slim


RUN apt-get update && apt-get install -y \
    build-essential \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .


# Create uploads directory
RUN mkdir -p uploads

# Set environment variables
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV GOOGLE_API_KEY=${GOOGLE_API_KEY}

# Expose port
EXPOSE 5001

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "run:app"] 