# Use the official Python image from the Docker Hub
FROM python:3.11.11-slim
# Set the working directory in the container
WORKDIR /app
# Copy the requirements file into the container
COPY requirements.txt .
# Install the dependencies specified in the requirements file
RUN pip install --no-cache-dir -r requirements.txt
# Copy the rest of the application code into the container
COPY . .

RUN pip install lib/ta_lib-0.6.3-cp311-cp311-win_amd64.whl

# Set the environment variable to tell Flask to run in production
ENV FLASK_ENV=production
# Expose the port on which the Flask app will run
EXPOSE 5000
# Command to run the Flask application
CMD ["flask", "run", "--host=0.0.0.0"]