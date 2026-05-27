# Apify actor: auto.ru parser

## Описание

Apify Actor для парсинга объявлений auto.ru — поиск по фильтрам (URL) или прямые карточки. Использует **Playwright** + **Python** стелс-обход.

- **Архитектура:** Apify SDK (Node.js entrypoint `main.js`) → вызывает Python-скрипты через `child_process`
- **Браузер:** Playwright с Chromium
- **Репо:** `https://github.com/fakaraev-hub/auto-ru-apify`

---

## Статус сборки

🟡 **В процессе фиксов Dockerfile** — последний коммит: `673d685`

---

## История изменений

### 1. Исходная ошибка — editor отсутствовал у полей schema

- **Симптом:** `Property filterSearchUrlInput must have "editor" property`
- **Фикс:** Добавлен `editor` (select / textfield / textarea / number) всем полям `.actor/INPUT_SCHEMA.json`
- **Коммит:** `4129921`

### 2. apt-get: not found

- **Симптом:** Базовый образ `apify/actor-node:20` — Alpine Linux, нет `apt-get`
- **Проблема:** Нужен Python + pip для запуска Playwright-скриптов
- **Фикс:** Смена base image на `apify/actor-node-puppeteer-chrome:20` (Debian-based)
- **Коммит:** `f793b54`

### 3. pip3: not found

- **Симптом:** В `actor-node-puppeteer-chrome` Python предустановлен, но `pip3` не в PATH
- **Фикс:** `RUN python3 -m pip install` вместо `RUN pip3 install`
- **Коммит:** `763f924`

### 4. python3: not found

- **Симптом:** Ожидалось, что `python3` есть в образе. Оказалось — нет
- **Фикс:** Возврат `apt-get install python3 python3-pip` (Debian-based образ поддерживает apt)
- **Коммит:** `8ef3965` → `673d685`

### 5. Конфликт playwright + playwright-stealth

- **Проблема:** `playwright-stealth` ставит свой Chromium, конфликтует с пакетным из образа
- **Фикс:** Убран `playwright-stealth` из `requirements.txt`. Используем нативный `playwright` — стелс достигается через `launch_args` и user-agent
- **Коммит:** `8ef3965`

---

## Текущий Dockerfile

```dockerfile
FROM apify/actor-node-puppeteer-chrome:20

USER root

RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

ENV PLAYWRIGHT_BROWSERS_PATH=0

COPY . .
ENV PYTHONPATH=/usr/src/app/src
CMD ["node", "main.js"]
```

## Текущий requirements.txt

```
playwright==1.45.0
apify-client==1.8.0
beautifulsoup4==4.12.3
lxml==5.2.2
```

---

## Следующий шаг (TODO)

- [ ] Пересобрать actor на Apify с коммита `673d685`
- [ ] Если сборка пройдёт — запустить тестовый run с `mode=discovery` + `searchUrl`
- [ ] Проверить, что Python-скрипты корректно вызываются из Node.js entrypoint
- [ ] Проверить вывод в `OUTPUT` dataset Apify

---

## Примечания

- Образ `apify/actor-node-puppeteer-chrome:20` — **Debian-based**, Chromium предустановлен для Puppeteer. Для Playwright используем системный Chromium (`PLAYWRIGHT_BROWSERS_PATH=0`).
- `main.js` — Node.js, вызывает `src/search_discovery.py` и `src/offer_scraper.py` через `spawn('python3', ...)`.
- Входные параметры описаны в `.actor/INPUT_SCHEMA.json`.

