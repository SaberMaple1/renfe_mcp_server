# Authentication and Security

This document describes the authentication and security features implemented in the Renfe MCP Server.

## Overview

The Renfe MCP Server now includes comprehensive security features:

- **API Key Authentication**: Secure access control using API keys
- **Rate Limiting**: Prevent abuse with configurable request limits
- **Security Logging**: Track authentication events and potential security issues
- **Input Validation**: Date bounds checking to prevent abuse
- **Configurable Security**: Environment-based configuration for different deployment scenarios

## Quick Start

### 1. Generate an API Key

```bash
# Generate a new API key and create .env file
python security.py generate-key
```

This will create a `.env` file with a secure random API key:

```bash
RENFE_API_KEY=06aa1747ae99064c4d8652856eceb64fd61fda6fb707521108d2ae0ab82ece1d
```

### 2. Configure Security Settings

Edit the `.env` file to customize security settings:

```bash
# Authentication
RENFE_ENABLE_AUTH=true
RENFE_API_KEY=your-api-key-here

# Rate Limiting
RENFE_RATE_LIMIT_ENABLED=true
RENFE_MAX_REQUESTS_PER_MINUTE=30
RENFE_MAX_REQUESTS_PER_HOUR=200
```

See `.env.example` for all available configuration options.

### 3. Test the Security System

```bash
# Run the security test suite
python test_security.py
```

This will verify:
- Authentication is working
- Rate limiting is configured correctly
- Security logging is enabled
- Configuration is valid

## Authentication

### How It Works

The server uses **API key authentication**:

1. Client provides an API key with each request
2. Server validates the key using secure hash comparison
3. Access is granted or denied based on validation

### API Key Storage

API keys can be stored in two ways:

**Option 1: Plain API Key (Development)**
```bash
RENFE_API_KEY=your-secret-key-here
```

**Option 2: Hashed API Key (Production - Recommended)**
```bash
RENFE_API_KEY_HASH=173096620be80e484e1e683de1898c80de8bce6e82e1174e52ac69e64a37cfdb
```

The hashed version is more secure as it doesn't store the plain key on the server.

### Using the API

When authentication is enabled, all MCP tool calls require an `api_key` parameter:

```python
# Example: Searching for trains with authentication
result = search_trains(
    origin="Madrid",
    destination="Barcelona",
    date="2025-11-20",
    api_key="your-api-key-here"
)
```

### Development Mode

For local development, you can disable authentication:

```bash
# .env
RENFE_ENABLE_AUTH=false
RENFE_DEV_MODE=true
```

**⚠️ WARNING: Never use DEV_MODE=true in production!**

## Rate Limiting

### Purpose

Rate limiting prevents abuse by restricting the number of requests a client can make within a time window.

### Default Limits

**Regular Requests** (search_trains, find_station):
- 30 requests per minute
- 200 requests per hour

**Price Scraping Requests** (get_train_prices):
- 5 requests per minute
- 30 requests per hour

Price requests have stricter limits because they involve web scraping which:
- Puts load on Renfe's website
- Takes longer to complete
- Could trigger IP blocking if overused

### Configuration

Customize rate limits in `.env`:

```bash
# Regular requests
RENFE_MAX_REQUESTS_PER_MINUTE=30
RENFE_MAX_REQUESTS_PER_HOUR=200

# Price requests
RENFE_MAX_PRICE_REQUESTS_PER_MINUTE=5
RENFE_MAX_PRICE_REQUESTS_PER_HOUR=30
```

### How It Works

- Rate limiting uses a **token bucket algorithm**
- Limits are enforced **per client** (identified by API key hash)
- Old requests are automatically cleaned up
- When limit is exceeded, client receives a clear error message

### Handling Rate Limit Errors

When a client exceeds rate limits, they receive:

```
❌ Rate limit exceeded: Maximum 5 requests per minute. Please wait before trying again.
```

## Security Logging

### Purpose

Security logging tracks:
- Authentication successes and failures
- Rate limit violations
- Access patterns
- Security events

### Log Location

Security logs are written to: `logs/security.log`

### Log Format

```
2025-11-17 10:30:45 - renfe.security - INFO - SECURITY EVENT: ACCESS_GRANTED
2025-11-17 10:31:12 - renfe.security - WARNING - SECURITY EVENT: AUTH_FAILURE
2025-11-17 10:32:05 - renfe.security - WARNING - SECURITY EVENT: RATE_LIMIT_EXCEEDED
```

### Privacy

By default, sensitive data is **redacted** from logs:

```bash
RENFE_LOG_SENSITIVE_DATA=false  # Recommended
```

When disabled:
- API keys are redacted
- Location data (origin/destination) is hashed
- User queries are not logged in plaintext

### Configuration

```bash
# Enable/disable security logging
RENFE_LOG_SECURITY_EVENTS=true

# Log sensitive data (not recommended for production)
RENFE_LOG_SENSITIVE_DATA=false
```

## Input Validation

### Date Bounds Checking

The server now validates date inputs to prevent abuse:

**Minimum Date**: Yesterday (1 day in the past)
**Maximum Date**: 365 days in the future

Invalid dates are rejected with clear error messages:

```
❌ Date 2026-12-01 is too far in the future.
   Maximum booking window is 365 days.
   Latest date: 2025-11-16
```

### Purpose

- Prevents resource exhaustion from impossible date queries
- Matches realistic train booking windows
- Reduces unnecessary load on data processing

## Security Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Tool Call                        │
│           (search_trains, find_station, etc.)           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              @require_auth Decorator                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 1. Extract API key                                │  │
│  │ 2. Verify authentication                          │  │
│  │ 3. Check rate limits                              │  │
│  │ 4. Log security event                             │  │
│  │ 5. Call actual function OR return error           │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴───────────┐
        ▼                        ▼
┌────────────────┐       ┌────────────────┐
│ Authentication │       │ Rate Limiter   │
│   Manager      │       │                │
│ - Verify key   │       │ - Track usage  │
│ - Hash compare │       │ - Enforce      │
│                │       │   limits       │
└────────────────┘       └────────────────┘
        │                        │
        └────────────┬───────────┘
                     ▼
        ┌─────────────────────────┐
        │   Security Logger       │
        │ - Log events            │
        │ - Sanitize data         │
        │ - Write to file         │
        └─────────────────────────┘
```

### Security Features

1. **Constant-Time Comparison**: Uses `secrets.compare_digest()` to prevent timing attacks
2. **Secure Random**: Uses `secrets` module (not `random`) for API key generation
3. **Hash Storage**: API keys can be stored as SHA-256 hashes
4. **Privacy by Default**: Sensitive data redaction enabled by default
5. **Token Bucket**: Fair rate limiting per client
6. **Audit Trail**: All security events logged with timestamps

## Deployment Scenarios

### Local Development

```bash
# .env
RENFE_ENABLE_AUTH=false
RENFE_RATE_LIMIT_ENABLED=false
RENFE_DEV_MODE=true
RENFE_LOG_SECURITY_EVENTS=true
```

- Authentication disabled for convenience
- Rate limiting disabled
- Security logging enabled for debugging

### Production

```bash
# .env
RENFE_ENABLE_AUTH=true
RENFE_RATE_LIMIT_ENABLED=true
RENFE_DEV_MODE=false
RENFE_API_KEY_HASH=<generated-hash>
RENFE_LOG_SECURITY_EVENTS=true
RENFE_LOG_SENSITIVE_DATA=false
```

- Authentication required
- Rate limiting enforced
- Hashed API key storage
- Privacy-compliant logging

### Claude Desktop Integration

When using with Claude Desktop, you can configure the API key in the MCP server config:

**Windows** (`%APPDATA%\Claude\claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "renfe": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\path\\to\\renfe_mcp",
        "run",
        "python",
        "main.py"
      ],
      "env": {
        "RENFE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**macOS/Linux**:
```json
{
  "mcpServers": {
    "renfe": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/renfe_mcp",
        "run",
        "python",
        "main.py"
      ],
      "env": {
        "RENFE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Troubleshooting

### "Authentication failed" error

**Problem**: Client receives authentication error

**Solutions**:
1. Check that `RENFE_API_KEY` is set in `.env`
2. Verify the API key matches what's configured
3. Check that `RENFE_ENABLE_AUTH=true` if you want authentication

### "Rate limit exceeded" error

**Problem**: Client is being throttled

**Solutions**:
1. Wait for the rate limit window to reset (1 minute or 1 hour)
2. Increase limits in `.env` if legitimate use case
3. Use different client IDs to distribute load

### Security logs not being created

**Problem**: No logs in `logs/security.log`

**Solutions**:
1. Check that `RENFE_LOG_SECURITY_EVENTS=true`
2. Verify `logs/` directory exists (created automatically)
3. Check file permissions

## Security Best Practices

### API Key Management

✅ **DO**:
- Generate strong random API keys using `python security.py generate-key`
- Store API keys in environment variables or secure vaults
- Use `.env` files (with proper `.gitignore`)
- Rotate API keys periodically
- Use hashed storage in production (`RENFE_API_KEY_HASH`)

❌ **DON'T**:
- Commit API keys to version control
- Share API keys in plain text
- Use weak or predictable keys
- Hardcode keys in source code
- Reuse keys across environments

### Rate Limiting

✅ **DO**:
- Set conservative limits for production
- Monitor rate limit violations in logs
- Adjust limits based on actual usage patterns
- Use stricter limits for expensive operations (price scraping)

❌ **DON'T**:
- Disable rate limiting in production
- Set excessively high limits
- Ignore rate limit violations in logs

### Logging

✅ **DO**:
- Enable security logging in all environments
- Review logs regularly for suspicious activity
- Keep `LOG_SENSITIVE_DATA=false` in production
- Rotate log files to prevent disk space issues
- Monitor for authentication failures

❌ **DON'T**:
- Disable security logging in production
- Log sensitive personal data
- Leave logs world-readable
- Ignore repeated authentication failures

## Security Enhancements Implemented

This security system addresses the **HIGH severity** finding from the security audit:

### Before (Vulnerable)

```python
@mcp.tool()
def search_trains(origin: str, destination: str, ...):
    # No authentication
    # No rate limiting
    # No access control
    # No audit logging
    ...
```

### After (Secure)

```python
@mcp.tool()
@require_auth(is_price_request=False)
def search_trains(origin: str, destination: str, api_key: str = None, ...):
    # ✅ API key authentication
    # ✅ Rate limiting (30/min, 200/hour)
    # ✅ Access control
    # ✅ Security logging
    # ✅ Input validation
    ...
```

## Additional Security Features

### Date Validation

- Prevents queries for dates > 365 days in the future
- Rejects dates in the past (except yesterday)
- Clear error messages for invalid dates

### Privacy Protection

- User queries hashed in logs (when `LOG_SENSITIVE_DATA=false`)
- API keys never logged in plaintext
- Sensitive fields automatically redacted

### Monitoring

- All access attempts logged
- Authentication failures tracked
- Rate limit violations recorded
- Audit trail for compliance

## Related Documentation

- [Security Audit Report](SECURITY_AUDIT.md) - Full security assessment
- [README.md](README.md) - General usage documentation
- [.env.example](.env.example) - Configuration reference

## Support

For security-related questions or to report vulnerabilities:

- **Issues**: [GitHub Issues](https://github.com/belgrano9/renfe_mcp_server/issues)
- **Security**: Report privately via GitHub Security Advisories

---

**Last Updated**: 2025-11-17
**Security Version**: v1.0.0
