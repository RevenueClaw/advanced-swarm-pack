# Amazon Creators API v1

Fetch Amazon product data and generate affiliate links via the Amazon Creators API.

---

## Configuration

Create `~/.openclaw/credentials/amazon_creators.env` with your private credentials:

```bash
AMAZON_CREATOR_CLIENT_ID=amzn1.application-oa2-client.xxx
AMAZON_CREATOR_CLIENT_SECRET=amzn1.oa2-cs.v1.xxx
PARTNER_TAG=vhicklegar011-20
PARTNER_TYPE=Associates
OAUTH_SCOPE=creatorsapi::default
```

Set secure permissions:
```bash
chmod 600 ~/.openclaw/credentials/amazon_creators.env
```

---

## Usage

```python
from amazon_creators_api_v1 import AmazonCreatorsAPI

api = AmazonCreatorsAPI()

# Get product by ASIN
product = api.get_item("B08N5WRWNW")
print(product["title"])
print(product["affiliate_link"])

# Search products
results = api.search_items(keywords="laptop", search_index="Electronics")
```

---

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/catalog/v1/getItems` | POST | Fetch specific ASINs |
| `/catalog/v1/searchItems` | POST | Search catalog |

---

## API Reference

**Base URL:** `https://creatorsapi.amazon`

**Required Headers:**
- `Authorization: Bearer {token}`
- `x-marketplace: www.amazon.com`
- `Content-Type: application/json`

**Token Endpoint:** `POST https://api.amazon.com/auth/o2/token`

---

## Placeholder Variables

Never commit real credentials. Use these placeholders in shared code:

- `{{AMAZON_CREATOR_CLIENT_ID}}`
- `{{AMAZON_CREATOR_CLIENT_SECRET}}`
- `{{PARTNER_TAG}}`
- `{{PARTNER_TYPE}}` (always "Associates")

---

## Fallback

If API is unavailable, skill automatically falls back to web scraping with `requests` + `BeautifulSoup`.

---

**Security:** Credentials loaded at runtime from secure local storage only. No secrets in shared/global versions.
