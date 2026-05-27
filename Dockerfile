FROM apify/actor-node-puppeteer-chrome:20

USER root

RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv libxml2-dev libxslt1-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY package*.json ./
RUN npm install --omit=dev

COPY requirements.txt .

# PEP 668 fix: install into venv
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Download patched CloakBrowser Chromium binary
ENV HOME=/root
RUN cloakbrowser install

COPY . .
ENV PYTHONPATH=/usr/src/app/src
CMD ["node", "main.js"]
