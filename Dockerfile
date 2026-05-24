FROM apify/actor-node:20

RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN python3 -m playwright install chromium

COPY . .
ENV PYTHONPATH=/usr/src/app/src
CMD ["node", "main.js"]
