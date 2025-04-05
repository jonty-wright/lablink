# Use a lightweight Python base image
FROM python:3.10-slim

# Install required system dependencies for Chrome and Chromedriver
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    xvfb \
    libnss3 \
    libgconf-2-4 \
    libxi6 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libxtst6 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    fonts-liberation \
    libappindicator3-1 \
    libgbm-dev \
    && rm -rf /var/lib/apt/lists/*

# Add Google Chrome repository and install Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*


# Set the working directory
WORKDIR /modular_bulk

# Copy application files
COPY requirements.txt /modular_bulk/requirements.txt

# Install Python dependencies
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy the remaining application files
COPY . /modular_bulk

# Set environment variable to ensure Chrome binary is detected
ENV PATH="/usr/bin/google-chrome:$PATH"

# Set the entry point for the application
CMD ["python", "transcribe.py"]