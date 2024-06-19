FROM python:3.10-slim-bullseye

# Set the working directory
WORKDIR /bot

# Install necessary packages
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 git

# Remove apt lists to reduce image size
RUN rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements.txt requirements.txt

# Upgrade pip and install the rest of the dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application's code
COPY . .

# Use a non-root user
RUN useradd -ms /bin/bash botuser
USER botuser

# Run the bot
CMD ["python", "bot.py"]