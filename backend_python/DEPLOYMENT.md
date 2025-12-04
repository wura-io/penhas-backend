# PenhaS Python Backend - Deployment Guide

## 🚀 Quick Start with Docker

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 10GB disk space

### Local Development

1. **Clone and setup**
```bash
cd backend_python
cp .env.example .env
# Edit .env with your configuration
```

2. **Start services**
```bash
docker-compose up -d
```

3. **Run migrations**
```bash
docker-compose exec api alembic upgrade head
```

4. **Access the API**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

### Production Deployment

#### 1. Build production image
```bash
docker build -t penhas-api:latest .
```

#### 2. Push to registry
```bash
docker tag penhas-api:latest your-registry/penhas-api:latest
docker push your-registry/penhas-api:latest
```

#### 3. Deploy with Docker Compose
```bash
# Update environment variables in .env
docker-compose -f docker-compose.prod.yml up -d
```

## 📦 Manual Installation

### System Requirements
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Poetry 1.7+

### Installation Steps

1. **Install dependencies**
```bash
cd backend_python
poetry install
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env file
```

3. **Run migrations**
```bash
poetry run alembic upgrade head
```

4. **Start services**

API Server:
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Celery Worker:
```bash
poetry run celery -A app.worker worker --loglevel=info
```

Celery Beat:
```bash
poetry run celery -A app.worker beat --loglevel=info
```

## 🔧 Configuration

### Required Environment Variables

```bash
# Database
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5432
POSTGRESQL_USER=postgres
POSTGRESQL_PASSWORD=secure_password
POSTGRESQL_DBNAME=penhas

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# JWT
SECRET_KEY=your_32_char_minimum_secret_key

# AWS
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_S3_BUCKET=your_bucket
AWS_SNS_REGION=sa-east-1

# External APIs
GOOGLE_MAPS_API_KEY=your_key
IWEBSERVICE_CPF_TOKEN=your_token
FIREBASE_SERVER_KEY=your_key

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user
SMTP_PASSWORD=password
SMTP_FROM=noreply@penhas.app.br
```

## 🔄 Database Migrations

### Create migration
```bash
alembic revision --autogenerate -m "description"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback
```bash
alembic downgrade -1
```

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/
```

### Metrics
Access `/maintenance/status` for system stats

### Logs
```bash
docker-compose logs -f api
docker-compose logs -f celery_worker
```

## 🔒 Security

### Production Checklist
- [ ] Change all default passwords
- [ ] Set strong SECRET_KEY (32+ characters)
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Enable Redis password
- [ ] Configure CORS properly
- [ ] Set up monitoring and alerts

### SSL/TLS Setup

Use a reverse proxy (nginx/traefik) for SSL termination:

```nginx
server {
    listen 443 ssl http2;
    server_name api.penhas.com.br;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose ps db
# Check logs
docker-compose logs db
```

### Redis Connection Issues
```bash
# Check Redis is running
docker-compose ps redis
# Test connection
redis-cli ping
```

### Celery Not Processing Tasks
```bash
# Check worker logs
docker-compose logs celery_worker
# Restart worker
docker-compose restart celery_worker
```

## 📈 Performance Tuning

### API Workers
Adjust `--workers` based on CPU cores:
```bash
workers = (2 × CPU cores) + 1
```

### Database Pool
Edit `app/db/session.py`:
```python
pool_size=20,
max_overflow=40
```

### Redis Memory
Configure in docker-compose.yml:
```yaml
redis:
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

## 🔄 Migration from Perl

### Parallel Running
Both Perl and Python APIs can run simultaneously against the same database:

1. Keep Perl API running
2. Deploy Python API on different port
3. Gradually migrate traffic
4. Monitor for issues
5. Decommission Perl when confident

### Data Compatibility
- 100% database schema compatibility
- Same JWT tokens work for both
- Sessions shared via Redis
- No data migration needed

## 📚 Additional Resources

- API Documentation: `/docs`
- Redoc Documentation: `/redoc`
- OpenAPI Schema: `/openapi.json`
- Health Check: `/maintenance/status`

## 🆘 Support

For issues or questions:
- Check logs: `docker-compose logs`
- Review API docs: http://localhost:8000/docs
- Check database: `psql -h localhost -U postgres -d penhas`

