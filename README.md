# Auto.ru Universal Parser (Apify Actor)

Парсинг auto.ru через Apify: поиск, карточки, мониторинг цен.

## Режимы

### search — поиск по фильтрам
```json
{
  "mode": "search",
  "brand": "BMW",
  "model": "X5",
  "priceMin": 3000000,
  "priceMax": 5000000,
  "yearMin": 2020,
  "maxPages": 3,
  "proxyConfiguration": {"useApifyProxy": true}
}
```

### card — парсинг карточки по URL
```json
{
  "mode": "card",
  "offerUrls": ["https://auto.ru/cars/used/sale/..."],
  "proxyConfiguration": {"useApifyProxy": true}
}
```

### monitor — мониторинг цен
```json
{
  "mode": "monitor",
  "offerUrls": ["url1", "url2", "url3"],
  "proxyConfiguration": {"useApifyProxy": true}
}
```

## Output

Apify Dataset (JSONL) — каждая строка = один объект.
