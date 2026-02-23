# Nikoo AI - Chatbot Assistant

A FastAPI-based AI chatbot powered by Google Gemini API that provides intelligent 24/7 support with context-aware conversations, thread management, RAG (Retrieval-Augmented Generation), and MongoDB integration.

## 🎯 Features

- **Context-Aware Conversations**: Multi-turn WebSocket conversations with thread management
- **RAG (Retrieval-Augmented Generation)**: Smart document context retrieval with FAISS indexing
- **Auto-Summary Generation**: Automatic conversation summaries
- **MongoDB Integration**: Persistent storage for threads and chat history
- **24/7 Availability**: Real-time AI-powered support via WebSocket
- **Multi-Language Support**: Responds in user's preferred language
- **Fast Responses**: Powered by Google Gemini API
- **Production-Ready**: Console logging, configurable CORS, environment-based settings
- **Docker Support**: Multi-stage Docker build for optimized deployment

## 📋 Requirements

- Python 3.11+ or Docker
- Google Gemini API Key (Get from https://ai.google.dev)
- MongoDB (local or cloud instance - MongoDB Atlas recommended)
- Dependencies in `requirements.txt`

## 🚀 Quick Start

### Option 1: Local Setup (Python Virtual Environment)

#### 1. Clone or Download the Project
```bash
cd Nikoo_ai_kyc_review
```

#### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
# Google Gemini API
GEMINI_API_KEY=your_google_gemini_api_key
GEMINI_MODEL=gemini-3-flash-preview
TEMPERATURE=0.7
MAX_TOKENS=1000

# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=nikoo_ai

# Application
API_TITLE=Nikoo AI Chatbot
API_VERSION=1.0.0
DEBUG=False

# CORS (Production)
CORS_ORIGINS=["http://localhost:3000"]
HOST=0.0.0.0
PORT=8000
```

**Get your Google Gemini API Key:**
1. Go to https://ai.google.dev
2. Sign up or log in with Google Account
3. Create an API key
4. Copy and paste it in `.env` file

#### 5. Ensure MongoDB is Running
```bash
# Local MongoDB (if installed)
mongod

# Or use MongoDB Atlas (cloud)
# Update MONGODB_URL with your connection string
```

#### 6. Run the Application
```bash
# Start the FastAPI server
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at: `http://127.0.0.1:8000`

---

### Option 2: Docker Setup

#### Prerequisites
- Docker installed on your system ([Download Docker](https://www.docker.com/products/docker-desktop))

#### 1. Configure Environment Variables
Create a `.env` file in the project root:
```env
# Google Gemini API
GEMINI_API_KEY=your_google_gemini_api_key
GEMINI_MODEL=gemini-3-flash-preview
TEMPERATURE=0.7
MAX_TOKENS=1000

# Database
MONGODB_URL=mongodb://mongo:27017
DATABASE_NAME=nikoo_ai

# Application
API_TITLE=Nikoo AI Chatbot
API_VERSION=1.0.0
DEBUG=False

# CORS
CORS_ORIGINS=["http://localhost:3000"]
HOST=0.0.0.0
PORT=8000
```

#### 2. Build and Run with Docker Compose
```bash
# Build and start the container
docker-compose up --build

# Run in background (detached mode)
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

#### 3. Or Build and Run Docker Image Manually
```bash
# Build the image
docker build -t chatbot-ai .

# Run the container
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_google_gemini_api_key \
  -e GEMINI_MODEL=gemini-3-flash-preview \
  -e MONGODB_URL=mongodb://localhost:27017 \
  -e DATABASE_NAME=nikoo_ai \
  chatbot-ai
```

The API will be available at: `http://localhost:8000`

#### Docker Compose Services
- **chatbot**: Main WebSocket API service running on port 8000
- **mongo**: MongoDB database service (if included in docker-compose.yml)

---

## 🐳 Docker Information

### Multi-Stage Dockerfile
The project uses an optimized multi-stage Docker build:

**Stage 1 (Builder):**
- Installs build dependencies (gcc, etc.)
- Compiles and installs Python packages
- Creates a clean build environment

**Stage 2 (Runtime):**
- Lightweight runtime image
- Copies only necessary Python packages from builder
- Excludes build tools for smaller image size
- Base image: `python:3.11-slim`
- Final image size: ~30% smaller than single-stage build

**Benefits:**
- ✅ Smaller image size (faster deployment)
- ✅ Enhanced security (no build tools in production)
- ✅ Faster container startup
- ✅ Reduced attack surface

### docker-compose.yml
- Automatically loads environment variables from `.env` file
- Includes MongoDB service for data persistence
- Network configuration for service communication
- Volume mapping for development
- Auto-restart policy enabled
- Health checks configured

### Common Docker Commands
```bash
# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# View container logs
docker logs chatbot-ai

# Stop container
docker stop chatbot-ai

# Remove container
docker rm chatbot-ai

# Remove image
docker rmi chatbot-ai
```

## 📚 API Endpoints

## 📚 API Endpoints

### Root Endpoint
```bash
GET /
```
**Response:**
```json
{
  "status": "AI running",
  "websocket_endpoint_example": "ws://localhost:8000/ws/chat/{thread_id}/{user_id}"
}
```

### WebSocket Chat Endpoint
```
ws://localhost:8000/ws/chat/{thread_id}/{user_id}
```

**Description:** Real-time chat via WebSocket with thread and user identification

**Parameters:**
- `thread_id`: Unique conversation thread identifier
- `user_id`: Unique user identifier

**Message Format (Send):**
```json
{
  "message": "Your question or message here",
  "context": "Optional context information"
}
```

**Message Format (Receive):**
```json
{
  "type": "response",
  "message": "AI response text",
  "thread_id": "thread_id",
  "timestamp": "2024-02-23T10:00:00"
}
```

---

## 🏗️ Project Structure

```
Nikoo_ai_kyc_review/
├── app/
│   ├── database/
│   │   ├── __init__.py
│   │   ├── AIchatbotDatabase.py      # MongoDB sync client
│   │   └── KYCdatabase.py            # Async MongoDB (commented - KYC removed)
│   ├── documents/
│   │   ├── content_policy.txt        # RAG knowledge base
│   │   ├── faq.txt                   # FAQs for RAG
│   │   └── faiss_index/              # Vector index for RAG
│   ├── LLM_Service/
│   │   └── ai_service.py             # Google Gemini integration
│   ├── logs/                          # Application logs (console only in production)
│   ├── models/
│   │   └── schemas.py                # Pydantic models
│   ├── prompts/
│   │   └── system_prompt.py          # AI system prompt
│   ├── routers/
│   │   └── AI_Chat_threads.py        # WebSocket chat endpoints
│   ├── services/
│   │   ├── context_manager.py        # Context handling
│   │   ├── rag_service.py            # RAG implementation
│   │   └── verification_service.py   # Verification logic
│   ├── schema/
│   │   └── schema.py                 # Data schemas
│   └── utils/
│       ├── auth.py                   # Authentication utilities
│       └── exceptions.py             # Custom exceptions
├── config.py                          # Environment configuration
├── main.py                            # FastAPI application entry
├── requirements.txt                   # Python dependencies
├── Dockerfile                         # Multi-stage Docker build
├── docker-compose.yml                 # Docker Compose services
└── README.md                          # This file
```

---

## ⚙️ Configuration

All settings are environment-based (see `.env` file):

**API Settings:**
- `API_TITLE`: API title (default: "Chatbot API")
- `API_VERSION`: API version (default: "1.0.0")
- `DEBUG`: Debug mode (default: False - must be False in production)

**LLM Settings:**
- `GEMINI_API_KEY`: Google Gemini API key (required)
- `GEMINI_MODEL`: Model name (default: "gemini-3-flash-preview")
- `TEMPERATURE`: Response creativity (0.0-1.0, default: 0.7)
- `MAX_TOKENS`: Maximum response length (default: 1000)

**Database Settings:**
- `MONGODB_URL`: MongoDB connection string
- `DATABASE_NAME`: Database name (default: "nikoo_ai")

**Server Settings:**
- `HOST`: Server host (default: "0.0.0.0" for Docker, "127.0.0.1" for local)
- `PORT`: Server port (default: 8000)
- `CORS_ORIGINS`: Allowed CORS origins (default: ["http://localhost:3000"])

---

## 🔒 Production Deployment Checklist

- ✅ Set `DEBUG=False` in environment
- ✅ Configure `CORS_ORIGINS` for your domains (not `["*"]`)
- ✅ Use strong `GEMINI_API_KEY` and MongoDB credentials
- ✅ Use MongoDB Atlas (cloud) instead of local MongoDB
- ✅ Enable logging via container logs (not file-based)
- ✅ Set `HOST=0.0.0.0` and configure reverse proxy (Nginx)
- ✅ Use HTTPS/TLS for WebSocket connections (wss://)
- ✅ Set up container orchestration (Kubernetes, Docker Swarm)
- ✅ Configure health checks and monitoring
- ✅ Use environment variables for all secrets (.env in container)

---

## 🛠️ Troubleshooting

### MongoDB Connection Failed
```
Error: Failed to connect to MongoDB
Solution: Ensure MongoDB is running and MONGODB_URL is correct
- Local: mongodb://localhost:27017
- Atlas: mongodb+srv://user:password@cluster.mongodb.net/database
```

### Google Gemini API Error
```
Error: GEMINI_API_KEY is invalid or expired
Solution:
1. Get new key from https://ai.google.dev
2. Update .env file
3. Restart application
```

### WebSocket Connection Failed
```
Error: WebSocket connection refused
Solution:
1. Ensure API is running on correct port
2. Check CORS_ORIGINS configuration
3. Use correct thread_id and user_id in URL
```

### Docker Build Fails
```
Error: Docker image build fails
Solution:
1. Ensure requirements.txt is valid
2. Check Dockerfile syntax
3. Increase Docker memory if needed
```

---

## 📝 Environment Variables Example

```env
# .env file (never commit to git)

# Required
GEMINI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx

# Optional (defaults will be used if not set)
GEMINI_MODEL=gemini-3-flash-preview
TEMPERATURE=0.7
MAX_TOKENS=1000

MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=nikoo_ai

API_TITLE=Nikoo AI Chatbot
API_VERSION=1.0.0
DEBUG=False

CORS_ORIGINS=["http://localhost:3000"]
HOST=0.0.0.0
PORT=8000
```

---

## 📜 License

This project is proprietary and confidential - Nikoo AI

## 🤝 Support

For issues or questions, contact the development team.
