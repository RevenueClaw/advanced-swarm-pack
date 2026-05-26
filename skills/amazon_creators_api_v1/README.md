# Amazon Creators API v1

## Quick Start

```python
from amazon_creators_api_v1 import AmazonCreatorsAPI

# Initialize (loads credentials from ~/.openclaw/credentials/)
api = AmazonCreatorsAPI()

# Get product by ASIN
product = api.get_item("B08N5WRWNW")
print(f"Title: {product.title}")
print(f"Price: {product.price}")
print(f"Affiliate: {product.affiliate_link}")
```

## Setup

```bash
# Copy example config and fill in your credentials
cp config.example.yaml ~/.openclaw/credentials/amazon_creators.env

# Edit with your real credentials
nano ~/.openclaw/credentials/amazon_creators.env

# Set secure permissions
chmod 600 ~/.openclaw/credentials/amazon_creators.env
```

## Security Notes

- Credentials stored in **private local storage only**
- Skill code uses **placeholder variables** only
- No secrets committed to version control
- Fallback to web scraping if API unavailable

## Placeholders Used

| Placeholder | Description |
|-------------|-------------|
| `{{AMAZON_CREATOR_CLIENT_ID}}` | AWS Application ID |
| `{{AMAZON_CREATOR_CLIENT_SECRET}}` | OAuth Client Secret |
| `{{PARTNER_TAG}}` | Associates tracking ID |

## CLI Usage

```bash
# Test with ASIN
python amazon_creators_api_v1.py --asin B08N5WRWNW

# Search keywords
python amazon_creators_api_v1.py --search "laptop"

# Use different partner tag
python amazon_creators_api_v1.py --asin B08N5WRWNW --partner-tag YOURTAG-20
```

## License

MIT - See advanced-swarm-pack root LICENSE
