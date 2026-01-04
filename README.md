# StayOnBoard Validation API

A production-ready FastAPI backend for brand and WCAG accessibility validation services.

## Features

- **Color Contrast Analysis**: Calculate contrast ratios and check WCAG compliance
- **Brand Validation**: Validate images against brand guidelines and color palettes
- **Color Extraction**: Extract dominant colors from images
- **Image Comparison**: Compare images for brand consistency
- **WCAG Validation**: Check images for accessibility compliance
- **Validation History**: Track and rerun past validations

## Project Structure

```
StayOnBrand-Backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration with pydantic-settings
│   ├── dependencies.py      # Dependency injection providers
│   ├── routers/             # API endpoint routers
│   │   ├── colors.py        # Color contrast endpoints
│   │   ├── brand.py         # Brand validation endpoints
│   │   ├── wcag.py          # WCAG validation endpoints
│   │   ├── validate.py      # Validation history endpoints
│   │   └── utils.py         # Utility endpoints
│   ├── services/            # Business logic layer
│   │   ├── auth_service.py
│   │   ├── brand_service.py
│   │   ├── color_service.py
│   │   ├── redis_service.py
│   │   ├── storage_service.py
│   │   ├── validation_service.py
│   │   └── wcag_service.py
│   ├── models/              # Pydantic models
│   │   ├── common.py
│   │   ├── enums.py
│   │   ├── requests.py
│   │   └── responses.py
│   ├── middleware/          # Custom middleware
│   │   └── error_handler.py
│   └── utils/               # Utility functions
│       ├── cache.py
│       └── file_validation.py
├── tests/
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- Redis (for caching and storage)
- Docker (optional, for containerized deployment)

### Local Development

1. **Clone and setup environment**

```bash
# Clone the repository
cd StayOnBrand-Backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. **Configure environment**

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# At minimum, set:
# - JWT_SECRET_KEY (generate a secure random key)
# - AUTH_SERVICE_URL (your authentication service)
```

3. **Start Redis**

```bash
# Using Docker
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Or install locally and start
redis-server
```

4. **Run the application**

```bash
# Development mode with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or run directly
python -m app.main
```

5. **Access the API**

- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs (debug mode only)
- ReDoc: http://localhost:8000/redoc (debug mode only)
- Health Check: http://localhost:8000/api/v1/health

### Docker Development

```bash
# Start all services
docker-compose up

# Start with Redis UI (for debugging)
docker-compose --profile debug up

# Rebuild after code changes
docker-compose up --build
```

### Production Deployment

```bash
# Build and start production containers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f api
```

## API Endpoints

### Color Contrast

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/colors/compare` | Compare color contrast ratio |

### Brand Validation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/brand/validate-image` | Validate image against brand |
| POST | `/api/v1/brand/extract-colors` | Extract colors from image |
| POST | `/api/v1/brand/compare-images` | Compare two images |

### WCAG Validation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/wcag/validate-image` | Validate image for WCAG |
| POST | `/api/v1/wcag/validate-text-contrast` | Validate text contrast |
| GET | `/api/v1/wcag/requirements` | Get WCAG requirements |

### Validation History

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/validate/history` | Get validation history |
| GET | `/api/v1/validate/{id}` | Get validation details |
| POST | `/api/v1/validate/{id}/rerun` | Rerun a validation |

### Utilities

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/utils/supported-formats` | Get supported formats |

## Authentication

All endpoints (except health check and supported formats) require JWT authentication.

Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

The API verifies tokens against an external authentication service configured via `AUTH_SERVICE_URL`.

## Configuration

Configuration is managed via environment variables. See `.env.example` for all available options.

Key settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `REDIS_HOST` | Redis hostname | `localhost` |
| `AUTH_SERVICE_URL` | External auth service URL | - |
| `JWT_SECRET_KEY` | Secret for local JWT verification | - |
| `MAX_FILE_SIZE_MB` | Maximum upload file size | `10` |

## Implementing Business Logic

The project is structured as a skeleton with TODO comments marking where business logic should be implemented.

### Key files to implement:

1. **Color Analysis** (`app/services/color_service.py`)
   - Implement `_calculate_luminance()` for accurate contrast calculations
   - Implement `generate_recommendations()` for accessible color suggestions

2. **Brand Validation** (`app/services/brand_service.py`)
   - Implement `_extract_colors_from_image()` for color extraction
   - Implement `_match_brand_colors()` for brand color matching
   - Implement `_calculate_similarity()` for image comparison

3. **WCAG Validation** (`app/services/wcag_service.py`)
   - Implement `_detect_wcag_issues()` for accessibility issue detection
   - Add comprehensive WCAG criteria database

4. **Storage** (`app/services/storage_service.py`)
   - Implement actual file storage (S3, filesystem, etc.)

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Code Formatting

```bash
# Install formatters
pip install black isort ruff

# Format code
black app tests
isort app tests

# Lint
ruff check app tests
```

### Type Checking

```bash
pip install mypy
mypy app
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
