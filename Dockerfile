FROM apify/actor-node-puppeteer-chrome:20

# Playwright + Chromium dependencies already pre-installed in this image
USER root

WORKDIR /usr/src/app
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt
RUN python3 -m playwright install chromium

COPY . .
ENV PYTHONPATH=/usr/src/app/src
CMD ["node", "main.js"]
