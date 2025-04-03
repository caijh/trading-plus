# Use the official Python image from the Docker Hub
FROM python:3.11.11-slim AS builder

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies specified in the requirements file
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential wget && \
    wget https://github.com/ta-lib/ta-lib/releases/download/v0.6.3/ta-lib-0.6.3-src.tar.gz && \
    tar -xvf ta-lib-0.6.3-src.tar.gz && \
    cd ta-lib-0.6.3 && \
    ./configure && \
    make && \
    make install && \
    cd .. && \
    pip install --no-cache-dir TA-Lib==0.6.3 -r requirements.txt && \
    apt-get purge -y build-essential wget && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* /ta-lib-0.6.3*

# Use a smaller base image for the final runtime
FROM python:3.11.11-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the built artifacts from the builder stage
COPY --from=builder /app /app

# Set the environment variable to tell Flask to run in production
ENV FLASK_ENV=production

# Expose the port on which the Flask app will run
EXPOSE 5000

# Command to run the Flask application
CMD ["python", "run.py"]
