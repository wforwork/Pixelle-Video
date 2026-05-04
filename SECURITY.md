# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

Please report security vulnerabilities via:

1. **GitHub Issues** (for non-sensitive issues)
2. **Email** (for sensitive vulnerabilities - contact maintainers)

When reporting, please include:

- Type of issue
- Full paths of source file(s) related to the manifestation
- Location of the affected source code
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue

## Security Features

### 1. API Key Authentication

**⚠️ IMPORTANT: Change the default API key in production!**

The default API key is:
```
pixelle-secure-key-change-me-in-production
```

To set your own API key, modify `api/config.py`:
```python
api_key: str = "your-secure-random-key-here"
```

**Usage:** All `/api/*` endpoints (except `/api/files/`) require the `X-API-Key` header:
```bash
curl -H "X-API-Key: your-key" https://your-server/api/video/generate/sync
```

### 2. Rate Limiting

Rate limiting is enabled by default to prevent abuse:

| Endpoint | Limit |
|----------|-------|
| General API | 60/min |
| Video generation | 10/min |
| Image generation | 30/min |

**Configuration in `api/config.py`:**
```python
rate_limit_enabled: bool = True
rate_limit_per_minute: int = 60
rate_limit_video_per_minute: int = 10
rate_limit_image_per_minute: int = 30
```

When rate limit is exceeded, the API returns `429 Too Many Requests`.

### 3. Request Logging

All requests are logged with:
- HTTP method and path
- Response status code
- Response time (ms)
- Client IP address

Logs are output via loguru with INFO level.

### 4. Path Traversal Protection

File access is restricted to whitelisted directories:
- `output/`
- `workflows/`
- `templates/`
- `bgm/`
- `resources/`
- `data/bgm/`
- `data/templates/`

### 5. CORS Configuration

**⚠️ Default is `*` (allow all origins) - change in production!**

For production, restrict CORS origins in `api/config.py`:
```python
cors_origins: list[str] = ["https://your-trusted-domain.com"]
```

## Security Best Practices

### Production Deployment Checklist

- [ ] Change default API key
- [ ] Set restrictive CORS origins
- [ ] Use Redis for rate limit storage (instead of in-memory)
- [ ] Use HTTPS
- [ ] Consider IP whitelisting
- [ ] Keep dependencies updated

### Environment Variables

For production deployments:
```bash
export API_KEY="your-secure-random-key"
export CORS_ORIGINS="https://your-domain.com,https://admin.your-domain.com"
```

### Dependencies

Keep dependencies updated:
```bash
uv sync
pip install -r requirements.txt
```
