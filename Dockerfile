ROM --platform=linux/amd64 python:3.9-slim-bullseye

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
# Using --no-cache-dir to ensure fresh downloads and avoid potential hash mismatches
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Command to run the application
CMD ["python", "main.py"]