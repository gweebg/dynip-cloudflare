# Use the official Python image as the base image.
FROM python:3.11

# Set environment variables.
ENV CLOUDFLARE_TOKEN=changeme
ENV ZONE_ID=changeme

# Set the working directory inside the container-
WORKDIR /app

# Copy the requirements file into the container.
COPY requirements.txt .

# Install the Python dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Define the command to run your application
CMD [ "python", "-m", "src.main" ]
