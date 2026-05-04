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

## Security Best Practices

### API Key Configuration

**⚠️ IMPORTANT: Change the default API key in production!**

The default API key is:
```
pixelle-secure-key-change-me-in-production
```

To set your own API key, modify `api/config.py`:
```python
api_key: str = "your-secure-random-key-here"
```

### Environment Variables

For production deployments, use environment variables:
```bash
export API_KEY="your-secure-random-key"
```

### CORS Configuration

For production, restrict CORS origins in `api/config.py`:
```python
cors_origins: list[str] = ["https://your-trusted-domain.com"]
```

### File Upload

- Maximum upload size: 100MB (configurable)
- Only files from `output/`, `workflows/`, `templates/`, `bgm/`, `resources/` directories are accessible
- Path traversal protection is implemented

### Dependencies

Keep dependencies updated:
```bash
uv sync
pip install -r requirements.txt
```

## Security Features

- **API Key Authentication**: All `/api/*` endpoints (except `/api/files/`) require `X-API-Key` header
- **Path Traversal Protection**: File access restricted to whitelisted directories
- **CORS Middleware**: Configurable cross-origin request handling
- **Request Logging**: Unauthorized access attempts are logged
