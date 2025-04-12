# Use the official Python image from the Docker Hub
FROM python:3.11.11-slim

# Set the working directory in the container
WORKDIR /app

COPY . .

RUN apt-get update

# 设置时区为 Asia/Shanghai
ENV TZ=Asia/Shanghai

RUN apt-get install -y tzdata && \
    ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

# Install the dependencies specified in the requirements file
RUN apt-get install -y build-essential git && \
    dpkg -i lib/ta-lib_0.6.3_amd64.deb && \
    pip install --no-cache-dir TA-Lib==0.6.3 -r requirements.txt && \
    apt-get autoremove -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the environment variable to tell Flask to run in production
ENV FLASK_ENV=production

# Expose the port on which the Flask app will run
EXPOSE 5000

# Command to run the Flask application
CMD ["python", "run.py"]
