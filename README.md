# 🎫 Guestbook API - Test Automation Project

> A comprehensive RESTful API with JWT authentication, rate limiting, and extensive test automation

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](tests/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Security](#security)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Rate Limiting](#rate-limiting)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Contributing](#contributing)

---

## 🎯 Overview

This is a production-ready Guestbook API built with Flask, featuring:
- **JWT Authentication** for secure access
- **Rate Limiting** to prevent abuse
- **Comprehensive Testing** with pytest, Playwright, and Locust
- **API Documentation** with Swagger/Flasgger
- **Security Headers** and best practices
- **Health Monitoring** endpoints
- **Webhook System** for event notifications

Perfect for learning API development, testing automation, and security best practices!

---

## ✨ Features

### 🔐 Authentication & Security
- JWT-based authentication
- Email verification system
- Password reset functionality
- Rate limiting on all endpoints
- Security headers (CSP, X-Frame-Options, etc.)
- Input sanitization and validation
- SQL injection protection

### 📝 Guestbook API
- CRUD operations for guestbook entries
- Pagination and filtering
- Search functionality
- Bulk operations
- Excel import/export
- Reactions system (👍 👎 ❤️ 😂 😮 😢 😡)

### 🛡️ Rate Limiting (NEW!)
- **Brute-force protection**: Max 5 login attempts/minute
- **Spam prevention**: Max 3 registrations/hour
- **DDoS mitigation**: Rate limits on all endpoints
- **Smart identification**: JWT-based for authenticated, IP-based for anonymous
- **Different limits** for read (100/min) vs write (30/min) operations

### 🧪 Testing
- **Unit Tests**: pytest with comprehensive coverage
- **API Tests**: Automated endpoint testing
- **E2E Tests**: Playwright for browser automation
- **Load Tests**: Locust for performance testing
- **Security Tests**: Bandit and safety checks
- **Rate Limit Tests**: 5 different test methods

### 📊 Monitoring
- Health check endpoints (`/health`, `/ready`)
- Request logging with timing
- Rate limit monitoring
- Performance metrics

---

## 🔒 Security

### Implemented Security Features

#### Rate Limiting
| Endpoint Type | Authenticated | Anonymous | Protection |
|--------------|---------------|-----------|------------|
| Login | 5/min, 20/h | 5/min, 20/h | Brute-force |
| Register | 3/h, 10/day | 3/h, 10/day | Spam |
| API Read | 100/min | 20/min | DDoS |
| API Write | 30/min | 5/min | Abuse |

See [RATE_LIMITING_README.md](RATE_LIMITING_README.md) for details.

#### Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`
- `Content-Security-Policy` with appropriate rules
- `Referrer-Policy: strict-origin-when-cross-origin`

#### Authentication
- JWT tokens with configurable expiration
- Password hashing with PBKDF2-SHA256
- Email verification required for activation
- Secure password reset flow

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd TestApiSkills
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (optional)
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   cd src
   python app.py  # Database will be created automatically
   ```

### Running the Application

```bash
cd src
python app.py
```

The API will be available at: **http://localhost:8080**

---

## 📚 API Documentation

### Swagger UI
Interactive API documentation available at:
- **URL**: http://localhost:8080/apidocs/
- **Features**: Try out endpoints, view request/response schemas
- **Authentication**: Use the "Authorize" button with your JWT token

### Key Endpoints

#### Authentication
```
POST /api/v1/login              - User login
POST /api/v1/register           - User registration
GET  /api/v1/verify-email       - Email verification
POST /api/v1/password-reset-request - Request password reset
POST /api/v1/password-reset     - Reset password
```

#### Guestbook
```
GET    /api/v1/guestbook        - List entries (with pagination)
POST   /api/v1/guestbook        - Create entry
GET    /api/v1/guestbook/:id    - Get single entry
PUT    /api/v1/guestbook/:id    - Update entry
DELETE /api/v1/guestbook/:id    - Delete entry
DELETE /api/v1/guestbook/bulk   - Bulk delete
POST   /api/v1/guestbook/import - Import from Excel
```

#### Rate Limiting
```
GET /api/v1/rate-limit/status   - Check rate limit status
```

#### Health
```
GET /health  - Health check
GET /ready   - Readiness check
```

---

## 🧪 Testing

### Quick Test - Rate Limiting

```bash
# Terminal 1: Start server
cd src && python app.py

# Terminal 2: Run rate limit tests
python scripts/test_rate_limiting.py
```

### Run All Tests

```bash
# Unit tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test file
pytest tests/test_rate_limiting.py -v
```

### Test Methods Available

1. **Pytest**: `pytest tests/test_rate_limiting.py -v`
2. **Interactive Python**: `python scripts/test_rate_limiting.py`
3. **Bash/Curl**: `./scripts/test_rate_limit_curl.sh`
4. **Manual Curl**: See [TEST_RATE_LIMITING_NU.md](TEST_RATE_LIMITING_NU.md)
5. **Swagger UI**: http://localhost:8080/apidocs/

---

## 🛡️ Rate Limiting

Rate limiting is implemented to protect against:
- **Brute-force attacks** on authentication endpoints
- **DDoS attacks** on all API endpoints
- **API abuse** and excessive resource consumption
- **Spam registrations** and email flooding

### Quick Test

```bash
# Test login rate limit (should get 429 on 6th request)
for i in {1..6}; do
  curl -X POST http://localhost:8080/api/v1/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}'
  echo
done
```

### Documentation
- **Quick Start**: [SNABBSTART_RATE_LIMITING.md](SNABBSTART_RATE_LIMITING.md) 🇸🇪
- **Test Guide**: [TEST_RATE_LIMITING_NU.md](TEST_RATE_LIMITING_NU.md) 🇸🇪
- **Complete Guide**: [docs/RATE_LIMITING_GUIDE.md](docs/RATE_LIMITING_GUIDE.md) 🇬🇧
- **Implementation**: [RATE_LIMITING_IMPLEMENTATION.md](RATE_LIMITING_IMPLEMENTATION.md) 🇸🇪
- **Summary**: [RATE_LIMITING_README.md](RATE_LIMITING_README.md) 🇬🇧

---

## 📁 Project Structure

```
TestApiSkills/
├── src/
│   ├── app.py                      # Main Flask application
│   ├── rate_limiter.py             # Rate limiting configuration
│   ├── database.py                 # Database utilities
│   ├── auth_helpers.py             # Authentication helpers
│   ├── logger_config.py            # Logging configuration
│   ├── health_check.py             # Health monitoring
│   ├── webhooks.py                 # Webhook system
│   └── blueprints/v1/              # API endpoints (v1)
│       ├── auth.py                 # Authentication routes
│       ├── guestbook.py            # Guestbook CRUD
│       ├── reactions.py            # Reactions system
│       ├── webhooks.py             # Webhook routes
│       └── rate_limit_test.py      # Rate limit testing
│
├── tests/                          # Test suite
│   ├── test_rate_limiting.py       # Rate limit tests
│   ├── test_api.py                 # API tests
│   └── ...                         # More tests
│
├── scripts/                        # Utility scripts
│   ├── test_rate_limiting.py       # Interactive rate limit test
│   └── test_rate_limit_curl.sh     # Bash curl test
│
├── docs/                           # Documentation
│   ├── RATE_LIMITING_GUIDE.md      # Complete rate limiting guide
│   ├── guides/                     # Feature guides
│   └── implementation/             # Implementation docs
│
├── data/                           # SQLite databases
├── static/                         # Static files (CSS, JS)
├── templates/                      # HTML templates
└── requirements.txt                # Python dependencies
```

---

## 📖 Documentation

### Rate Limiting Documentation 🆕
- [🚀 Quick Start (Swedish)](SNABBSTART_RATE_LIMITING.md)
- [🧪 Test Guide (Swedish)](TEST_RATE_LIMITING_NU.md)
- [📘 Complete Guide (English)](docs/RATE_LIMITING_GUIDE.md)
- [📊 Implementation Summary (Swedish)](RATE_LIMITING_IMPLEMENTATION.md)
- [📄 Main README (English)](RATE_LIMITING_README.md)

### Other Documentation
- [Swagger Guide](docs/guides/SWAGGER_GUIDE.md)
- [Logging Guide](docs/guides/LOGGING_GUIDE.md)
- [Playwright Guide](docs/guides/PLAYWRIGHT_GUIDE.md)
- [Test Data Management](docs/guides/TEST_DATA_MANAGEMENT.md)

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Application
SECRET_KEY=your-secret-key-change-in-production
APP_BASE_URL=http://localhost:8080
ENVIRONMENT=development

# Rate Limiting
RATE_LIMIT_DEFAULT=1000 per hour, 100 per minute
RATE_LIMIT_STORAGE_URI=memory://  # or redis://localhost:6379

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=noreply@example.com
EMAIL_USE_TLS=true

# Registration
ENABLE_SELF_REGISTRATION=true
VERIFICATION_TOKEN_EXPIRATION_HOURS=24
PASSWORD_RESET_TOKEN_EXPIRATION_HOURS=2
```

### Rate Limiting Configuration

Edit `src/app.py` to customize rate limits:

```python
# Example: Change login limit
limiter.limit("10 per minute, 40 per hour")(
    app.view_functions.get("auth_v1.login")
)
```

---

## 🚀 Production Deployment

### Using Redis for Rate Limiting

```bash
# Install Redis
pip install redis

# Set environment variable
export RATE_LIMIT_STORAGE_URI="redis://localhost:6379"

# Run application
cd src && python app.py
```

### Docker Deployment

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  api:
    build: .
    ports:
      - "8080:8080"
    environment:
      - RATE_LIMIT_STORAGE_URI=redis://redis:6379/0
      - ENVIRONMENT=production
    depends_on:
      - redis
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Run tests before committing
pytest tests/ -v
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Flask for the excellent web framework
- Flask-Limiter for rate limiting functionality
- pytest for the testing framework
- Playwright for E2E testing
- All contributors and maintainers

---

## 📞 Support

For questions, issues, or suggestions:
- **Issues**: Open an issue on GitHub
- **Documentation**: Check the [docs/](docs/) folder
- **Rate Limiting**: See [RATE_LIMITING_README.md](RATE_LIMITING_README.md)

---

## 🎯 Quick Links

- **API Docs**: http://localhost:8080/apidocs/
- **Health Check**: http://localhost:8080/health
- **Rate Limit Status**: http://localhost:8080/api/v1/rate-limit/status

---

**Built with ❤️ using Flask, Python, and best practices**

*Last Updated: March 2024*
