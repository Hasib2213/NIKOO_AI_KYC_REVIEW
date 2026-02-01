# Nikoo AI - Mobile App Support Assistant

A powerful FastAPI-based AI chatbot powered by Groq API that provides intelligent 24/7 support for mobile applications with context-aware conversations, thread management, and MongoDB integration.

## 🎯 Features

- **Context-Aware Conversations**: Multi-turn conversations with thread management
- **Auto-Summary Generation**: Automatic conversation summaries every 10 messages
- **MongoDB Integration**: Persistent storage for threads and chat history
- **24/7 Availability**: Real-time AI-powered support
- **Multi-Language Support**: Responds in user's preferred language
- **Fast Responses**: Powered by Groq's fast LLM inference
- **Streamlit Dashboard**: Interactive web interface for testing
- **REST API**: Easy integration with frontend applications
- **Multi-Stage Docker Build**: Optimized Docker image for production
- **Health Monitoring**: Built-in health check endpoints

## 📋 Requirements

- Python 3.11+ or Docker
- Groq API Key (Get from https://console.groq.com)
- MongoDB (local or cloud instance)
- Dependencies: FastAPI, Uvicorn, Groq, Pydantic, PyMongo, Streamlit

## 🚀 Quick Start

### Option 1: Local Setup (Python Virtual Environment)

#### 1. Clone or Download the Project
```bash
cd nikoo_ai
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
GROQ_API_KEY=your_groq_api_key_here
MODEL=llama-3.3-70b-versatile
TEMPERATURE=0.7
MAX_TOKENS=1000
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=nikoo_ai_db
```

**Get your API Key:**
1. Go to https://console.groq.com
2. Sign up or log in
3. Create an API key
4. Copy and paste it in `.env` file

#### 5. Run the Application
```bash
# Option A: FastAPI Backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Option B: Streamlit Dashboard (in separate terminal)
streamlit run streamlit_app.py
```

The API will be available at: `http://127.0.0.1:8000`  
The Streamlit app will be at: `http://localhost:8501`

---

### Option 2: Docker Setup

#### Prerequisites
- Docker installed on your system ([Download Docker](https://www.docker.com/products/docker-desktop))

#### 1. Configure Environment Variables
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
MODEL=llama-3.3-70b-versatile
TEMPERATURE=0.7
MAX_TOKENS=1000
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=nikoo_ai_db
```

#### 2. Build and Run with Docker Compose
```bash
# Build and start the container
docker-compose up --build

# Run in background (detached mode)
docker-compose up -d --build

# View logs
docker-compose logs -f chatbot

# Stop the container
docker-compose down
```

#### 3. Or Build and Run Docker Image Manually
```bash
# Build the image
docker build -t chatbot-ai .

# Run the container
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your_groq_api_key_here \
  -e MODEL=llama-3.3-70b-versatile \
  -e TEMPERATURE=0.7 \
  -e MAX_TOKENS=1000 \
  chatbot-ai
```

The API will be available at: `http://localhost:8000`

#### Docker Compose Services
- **chatbot**: Main API service running on port 8000

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

### Health Check
```bash
GET /health
```
**Response:**
```json
{
  "status": "ok",
  "model": "llama-3.3-70b-versatile",
  "database": "connected"
}
```

### Context-Aware Chat (Recommended)
```bash
POST /api/chat
```

**Request:**
```json
{
  "user_id": "user123",
  "thread_id": "optional-thread-id",
  "content": "How do I add money to my wallet?"
}
```

**Response:**
```json
{
  "response": "To add money:\n- Go to Wallet → + Add Credits\n- Choose amount ($10, $25, $50, $100, $250, $500 or custom)\n- Pay with card → Balance added instantly.",
  "thread_id": "uuid-thread-id",
  "message_count": 2,
  "success": true,
  "error": null
}
```

### Generate Summary
```bash
POST /api/summary
```

**Request:**
```json
{
  "thread_id": "uuid-thread-id",
  "user_id": "user123"
}
```

**Response:**
```json
{
  "summary": "User inquired about adding money to wallet and was provided with step-by-step instructions...",
  "success": true,
  "error": null
}
```

### List User Threads
```bash
GET /api/threads?user_id=user123
```

**Response:**
```json
{
  "threads": [
    {
      "thread_id": "uuid-1",
      "message_count": 10,
      "created_at": "2026-01-20T10:30:00",
      "updated_at": "2026-01-20T11:45:00",
      "summary": "Discussion about wallet features"
    }
  ],
  "count": 1
}
```

### Get Thread Messages
```bash
POST /api/thread/messages
```

**Request:**
```json
{
  "thread_id": "uuid-thread-id",
  "user_id": "user123",
  "limit": 50
}
```

### Delete Thread
```bash
DELETE /api/thread/{thread_id}?user_id=user123
```

## 📁 Project Structure

```
nikoo_ai/
├── main.py                    # FastAPI application & endpoints
├── config.py                  # Configuration settings
├── streamlit_app.py          # Streamlit dashboard
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables
├── Dockerfile                # Multi-stage Docker build
├── docker-compose.yml        # Docker Compose setup
├── README.md                 # Documentation
└── app/
    ├── database.py           # MongoDB connection & operations
    ├── LLM_Service/
    │   └── ai_service.py     # Groq AI service & context management
    ├── prompts/
    │   └── system_prompt.py  # System prompts for AI
    └── schema/
        └── schema.py         # Pydantic models & validation
```

## 🔧 Configuration

Create a `.env` file in the project root:

```env
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here
MODEL=llama-3.3-70b-versatile
TEMPERATURE=0.7
MAX_TOKENS=1000

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=nikoo_ai_db

# Optional: MongoDB Atlas (Cloud)
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
```

**Get your Groq API Key:**  
Visit: https://console.groq.com → Create API Key

**MongoDB Setup:**
- Local: Install MongoDB Community Edition
- Cloud: Use MongoDB Atlas (free tier available)

## 📚 API Endpoints

### Health Check
```bash
GET /health
```

### Context-Aware Chat
```bash
POST /api/chat
```

**Request:**
```json
{
  "user_id": "user123",
  "thread_id": "optional-thread-id",
  "content": "Your question here"
}
```

**Response:**
```json
{
  "response": "AI response here",
  "thread_id": "uuid-thread-id",
  "message_count": 2,
  "success": true,
  "error": null
}
```

## 📝 Example Requests

### Using cURL
```bash
# Context-aware chat
curl -X POST 'http://127.0.0.1:8000/api/chat' \
  -H 'Content-Type: application/json' \
  -d '{
  "user_id": "user123",
  "content": "How do I reset my password?"
}'

# Get user threads
curl -X GET 'http://127.0.0.1:8000/api/threads?user_id=user123'

# Generate summary
curl -X POST 'http://127.0.0.1:8000/api/summary' \
  -H 'Content-Type: application/json' \
  -d '{
  "thread_id": "your-thread-id",
  "user_id": "user123"
}'
```

### Using Python
```python
import requests

# Context-aware chat
response = requests.post(
    'http://127.0.0.1:8000/api/chat',
    json={
        'user_id': 'user123',
        'content': 'How do I reset my password?'
    }
)
print(response.json())

# List threads
threads = requests.get(
    'http://127.0.0.1:8000/api/threads',
    params={'user_id': 'user123'}
)
print(threads.json())
```

### Using JavaScript
```javascript
// Context-aware chat
const response = await fetch('http://127.0.0.1:8000/api/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    user_id: "user123",
    content: "How do I reset my password?"
  })
});
const data = await response.json();
console.log(data);

// List threads
const threads = await fetch('http://127.0.0.1:8000/api/threads?user_id=user123');
const threadData = await threads.json();
console.log(threadData);
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `GROQ_API_KEY not configured` | Check `.env` file, get key from https://console.groq.com |
| `MongoDB connection failed` | Ensure MongoDB is running (local) or check URI for cloud |
| `Model has been decommissioned` | Update MODEL in `.env` to supported model |
| `Address already in use` | Change port: `uvicorn main:app --port 8001` |
| `Connection refused` | Ensure uvicorn is running and internet is connected |
| `Empty response` | Check max_tokens setting and message content |
| `Database not connected` | Verify MONGODB_URI and DATABASE_NAME in `.env` |
| `Thread not found` | Ensure thread_id exists and belongs to user_id |

## 💡 Key Features Explained

### Context-Aware Conversations
- Each user can have multiple conversation threads
- Messages are stored with context for better responses
- AI can reference previous messages in the same thread
- Automatic thread creation on first message

### Auto-Summary Generation
- System automatically generates summaries every 10 messages
- Summaries help in quick conversation overview
- Stored in MongoDB for future reference
- Can be manually triggered via API

### Thread Management
- Create, list, and delete conversation threads
- Each thread maintains its own context
- Thread metadata includes message count and timestamps
- Easy retrieval of conversation history

## 🔐 Security

- API keys are protected in `.env` (not committed to Git)
- Input validation on all endpoints with Pydantic
- User-based thread isolation (users can only access their own threads)
- Environment variables stored locally only
- Error handling prevents sensitive data leakage
- MongoDB connection secured with authentication options
- Multi-stage Docker build reduces attack surface

## 🚀 Production Deployment

### Docker Deployment (Recommended)
```bash
# Build and deploy
docker-compose up -d --build

# View logs
docker-compose logs -f

# Scale if needed
docker-compose up -d --scale chatbot=3
```

### Environment Variables for Production
```env
GROQ_API_KEY=your_production_key
MODEL=llama-3.3-70b-versatile
TEMPERATURE=0.5
MAX_TOKENS=1500
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
DATABASE_NAME=nikoo_ai_production
```

### Best Practices
- Use MongoDB Atlas for production database
- Enable MongoDB authentication
- Set up proper logging and monitoring
- Use environment-specific `.env` files
- Configure CORS for your frontend domain
- Set up SSL/TLS certificates
- Use Docker secrets for sensitive data

## 📊 Streamlit Dashboard

The project includes an interactive Streamlit dashboard for testing:

```bash
streamlit run streamlit_app.py
```

**Features:**
- User ID input
- Thread selection
- Real-time chat interface
- Thread history viewer
- Summary generation
- Message count display

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **AI/LLM**: Groq API (Llama 3.3 70B)
- **Database**: MongoDB
- **Frontend**: Streamlit (Dashboard)
- **Containerization**: Docker, Docker Compose
- **Validation**: Pydantic v2
- **Server**: Uvicorn (ASGI)

## 📈 Performance

- **Response Time**: < 2 seconds (with Groq)
- **Docker Image Size**: ~450MB (multi-stage build)
- **Memory Usage**: ~200MB (idle)
- **Concurrent Users**: Scales with Uvicorn workers
- **Database**: MongoDB handles thousands of threads

## 📄 License

This project is part of the Nikoo AI Mobile App Support Platform.

---

**Developed with ❤️ for intelligent customer support**

**Contact:** nikoo@app.com  
**Version:** 2.0.0  
**Last Updated:** January 2026
