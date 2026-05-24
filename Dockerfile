FROM apify/actor-node-puppeteer-chrome:20

USER root

# Универсальная установка Python (Debian/Ubuntu или Alpine)
RUN if command -v apt-get >/dev/null 2>&1; then \
        apt-get update && \
        apt-get install -y python3 python3-pip && \
        rm -rf /var/lib/apt/lists/*; \
    elif command -v apk >/dev/null 2>&1; then \
        apk update && \
        apk add --no-cache python3 py3-pip; \
    else \
        echo "No package manager found"; \
        exit 1; \
    fi

WORKDIR /usr/src/app
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Используем системный Chromium (уже есть в образе для Puppeteer)
ENV PLAYWRIGHT_BROWSERS_PATH=0

COPY . .
ENV PYTHONPATH=/usr/src/app/src
CMD ["node", "main.js"]
