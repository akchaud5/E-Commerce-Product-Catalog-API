# E-Commerce Product Catalog API

A high-performance, scalable RESTful API for managing e-commerce product catalogs, built with FastAPI and MongoDB.

## Features

- **High Performance**: Asynchronous API endpoints with FastAPI
- **Scalable Architecture**: Microservices-ready design with proper separation of concerns
- **Robust Authentication**: JWT-based auth with role-based access control
- **Advanced Data Handling**: MongoDB for flexible schema and high throughput
- **Extensive Documentation**: Auto-generated OpenAPI docs
- **Comprehensive Testing**: 90%+ test coverage with pytest
- **CI/CD Ready**: GitHub Actions workflow included
- **Docker Support**: Docker and docker-compose for easy deployment
- **Production Deployment**: Ready for deployment on Render or other cloud platforms

## Tech Stack

- **FastAPI**: Modern, high-performance web framework
- **MongoDB**: NoSQL database for flexible and scalable data storage
- **Motor**: Asynchronous MongoDB driver
- **Pydantic**: Data validation and settings management
- **JWT (jose)**: Secure authentication mechanism
- **Passlib & Bcrypt**: Password hashing and verification
- **Docker**: Containerization for consistent deployment
- **Pytest**: Comprehensive testing framework

## Getting Started

### Prerequisites

- Python 3.9+
- MongoDB (local or Atlas)
- Docker & Docker Compose (optional)

### Installation

#### Option 1: Local Development

1. Clone the repository
```bash
git clone <repository-url>
cd e-commerce-api
```

2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables (create a .env file)
```
MONGODB_URL=mongodb://localhost:27017/ecommerce
SECRET_KEY=your_secret_key_for_dev_only_please_change_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=dev
```

5. Start MongoDB (if not using Atlas)
```bash
# Either run MongoDB locally or use Docker:
docker run -d -p 27017:27017 --name mongodb mongo:6
```

6. Run the application
```bash
uvicorn app.main:app --reload
```

7. Access the API documentation at `http://localhost:8000/docs`

#### Option 2: Using Docker Compose

1. Clone the repository
```bash
git clone <repository-url>
cd e-commerce-api
```

2. Start the application with Docker Compose
```bash
docker-compose up -d
```

3. Access the API documentation at `http://localhost:8000/docs`

## API Endpoints

### Authentication
- `POST /api/v1/auth/register`: Register a new user
- `POST /api/v1/auth/login`: Login and get access token

### Products
- `GET /api/v1/products`: List all products (with pagination, filtering, and search)
- `GET /api/v1/products/{id}`: Get product details
- `POST /api/v1/products`: Create a new product (admin only)
- `PUT /api/v1/products/{id}`: Update a product (admin only)
- `DELETE /api/v1/products/{id}`: Delete a product (admin only)

### Categories
- `GET /api/v1/categories`: List all categories
- `GET /api/v1/categories/{id}`: Get category details
- `POST /api/v1/categories`: Create a new category (admin only)
- `PUT /api/v1/categories/{id}`: Update a category (admin only)
- `DELETE /api/v1/categories/{id}`: Delete a category (admin only)
- `GET /api/v1/categories/{id}/products`: List products by category

### Users
- `GET /api/v1/users/me`: Get current user profile
- `PUT /api/v1/users/me`: Update user profile
- `GET /api/v1/users`: List all users (admin only)
- `GET /api/v1/users/{id}`: Get user details (admin only)

## Database Setup

The application initializes the database with sample data when running in development mode. This includes:
- Admin user: email: `admin@example.com`, password: `admin123`
- Sample categories: Electronics, Clothing, Books, etc.
- Sample products in each category

## Testing

Run tests with pytest:
```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=app
```

## Deployment

### Render Deployment

This application is ready for deployment on Render using the included `render.yaml` configuration.

#### Option 1: One-click deployment

1. Fork this repository to your GitHub account
2. Visit the Render Dashboard: https://dashboard.render.com/
3. Click "New" and select "Blueprint" from the dropdown
4. Connect your GitHub account and select your forked repository
5. Click "Apply Blueprint"
6. Render will automatically set up the services defined in `render.yaml`

#### Option 2: Manual configuration

1. Push the code to a GitHub repository
2. Connect your Render account to GitHub
3. Create a new Web Service on Render, pointing to your repository
4. Configure environment variables:
   - `MONGODB_URL`: Your MongoDB connection string
   - `SECRET_KEY`: A secure random string
   - `ALGORITHM`: HS256
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: 30
   - `ENVIRONMENT`: prod
5. Configure the build command: `pip install -r requirements.txt`
6. Configure the start command: `gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
7. Deploy!

### Other Cloud Platforms

The application is Docker-ready and can be deployed to any platform that supports Docker containers.

## Development

### Project Structure

```
app/
├── api/               # API endpoints
│   ├── deps.py        # Dependencies
│   └── v1/            # API v1 endpoints
├── core/              # Core functionality
│   ├── config.py      # Configuration
│   └── security.py    # Security utilities
├── db/                # Database
│   ├── init_db.py     # Database initialization
│   └── mongodb.py     # MongoDB connection
├── models/            # Pydantic models for database
├── schemas/           # Pydantic schemas for API
├── services/          # Business logic
└── main.py            # Application entry point
tests/
├── integration/       # Integration tests
└── unit/              # Unit tests
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.