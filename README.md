# ExamForge

A website to make your own test papers from PDF documents using the help of LLM.

## Prerequisites

- **Local Development**: Node.js 18+, Python 3.11+
- **Docker Development**: Docker and Docker Compose

## Quick Start

### Option 1: Docker (Recommended)

1. **Clone the repository**

2. **Setup Environment**:
   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY to .env
   ```

3. **Start with Docker Compose**:
   ```bash
   docker-compose up
   ```
   
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000

4. **Stop the application**:
   ```bash
   docker-compose down
   ```

### Option 2: Local Development

1. **Clone the repository**

2. **Setup Environment**:
   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY to .env
   ```

3. **Run the App**:
   ```bash
   ./run_app.sh
   ```
   This script handles both backend and frontend startup.

## Docker Commands

### Development Mode (with hot-reload)
```bash
# Start services
docker-compose up

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Mode
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.prod.yml up -d
```

### Useful Commands
```bash
# Rebuild images after dependency changes
docker-compose build

# Remove all containers, networks, and volumes
docker-compose down -v

# Access backend shell
docker-compose exec backend bash

# Access frontend shell
docker-compose exec frontend sh

# View backend logs
docker-compose logs -f backend

# View frontend logs
docker-compose logs -f frontend
```

## Structure

- `frontend/`: React + Vite application (Memphis design style)
- `backend/`: Python FastAPI server
- `docker-compose.yml`: Docker orchestration for development
- `.env`: Environment configuration (copy from `.env.example`)

## Environment Variables

See `.env.example` for all available configuration options:
- `GEMINI_API_KEY`: Required for AI-powered question search
- `PORT`: Backend server port (default: 8000)
- `ENV`: Environment mode (development/production)
- `UPLOAD_DIR`: Directory for uploaded PDFs
- `OUTPUT_DIR`: Directory for generated exam PDFs

## Production Deployment (AWS EC2)

### Quick Deploy

1. **Launch EC2 Instance** (t3.micro or larger, Ubuntu 22.04)
2. **Setup Server**:
   ```bash
   sudo bash deploy/setup-ec2.sh
   ```
3. **Clone and Configure**:
   ```bash
   git clone <your-repo-url>
   cd ExamForge
   cp .env.production .env
   # Add your GEMINI_API_KEY to .env
   ```
4. **Deploy**:
   ```bash
   bash deploy/deploy.sh
   ```

### Access
Your app will be available at: `http://YOUR_EC2_PUBLIC_IP`

**📖 Full Deployment Guide**: See [docs/AWS-DEPLOYMENT.md](docs/AWS-DEPLOYMENT.md) for complete instructions including:
- EC2 instance setup
- Security configuration
- Troubleshooting
- Monitoring and maintenance
- Cost optimization

## Troubleshooting

### Docker Issues

**Port already in use**:
```bash
# Check what's using the port
lsof -i :8000  # or :5173
# Kill the process or change port in docker-compose.yml
```

**Permission errors with volumes**:
```bash
# Fix permissions for storage directory
sudo chown -R $USER:$USER ./backend/storage
```

**Changes not reflecting**:
```bash
# Rebuild containers
docker-compose up --build
```

### General Issues

**PDF processing fails**: Ensure GEMINI_API_KEY is set correctly in `.env`

**Storage issues**: Check that storage directories exist and have write permissions

## Features

- Upload and process PDF documents
- AI-powered question extraction using Google Gemini
- Search and filter questions
- Generate custom exam papers
- Page cropping and selection
- Real-time preview of selected pages

