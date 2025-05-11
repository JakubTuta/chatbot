# Use the official Python image from the Docker Hub
FROM python:3.13.3-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Replace the context in the djongo/models/fields.py file
RUN python replace_context.py

# Set the environment variable
ENV DOCKER=true

# Expose the port the application runs on
EXPOSE 8000

# Specify the command to run the application
CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]