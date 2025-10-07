# Kleio.ai 🏠✨

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6.svg)](https://www.typescriptlang.org/)

> **AI-Powered Household Inventory Management System for Indian Families**

Kleio.ai is an intelligent household assistant that helps Indian families track groceries, predict consumption patterns, reduce waste, and simplify meal planning—all while understanding the unique cultural context of Indian festivals, multi-generational living, and regional preferences.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [API Keys Setup](#api-keys-setup)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)
- [AI Features](#-ai-features)
- [Database Schema](#-database-schema)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 Features

### Core Features (MVP)

#### 🗂️ **Smart Inventory Management**
- **Manual Entry**: Quick add with auto-complete for categories and units
- **Photo-Based Entry**: Upload receipt/bill photos—AI extracts items automatically (Gemini Vision)
- **Real-time Tracking**: Monitor quantities, expiry dates, and stock levels
- **Categories**: 15+ predefined categories (vegetables, fruits, dairy, grains, spices, etc.)
- **Status Management**: Track items as active, consumed, expired, or discarded

#### 🍳 **AI Recipe Generation**
- Generate recipes from available inventory using **Google Gemini 2.5 Flash**
- Filter by cooking time, meal type, and cuisine preference
- Optimized for Indian recipes with regional variations
- Shows ingredient availability and what you need to buy
- Respects dietary preferences (vegetarian, vegan, diabetic, gluten-free)

#### 🛒 **Smart Shopping Lists**
- **Pattern-Based Predictions**: Learns your consumption patterns over time
- **Automatic Generation**: Predicts when items will run out
- **Urgency Categorization**: Urgent, soon, or plan-ahead items
- **Festival Intelligence**: Pre-configured shopping lists for 10+ major Indian festivals
- **Guest Calculation**: Adjust quantities based on number of guests

#### 🤖 **Conversational AI Assistant**
- Natural language interface powered by **LangChain + Gemini**
- "I bought tomatoes and milk" → Auto-adds to inventory
- "What can I cook?" → AI suggests recipes
- "What should I buy?" → Generates shopping list
- Context-aware conversations with memory

#### 🎉 **Festival Calendar**
- Pre-loaded with major Indian festivals (Diwali, Holi, Pongal, Onam, etc.)
- Region-specific festival shopping lists
- Quantity calculations for gatherings
- Timely reminders before festivals

#### 📊 **Pattern Recognition**
- Tracks purchase and consumption patterns
- Calculates average days between purchases
- Predicts depletion dates
- Suggests optimal purchase quantities
- Confidence scoring for predictions

---

## 🏗️ Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (React + Vite)                      │
│              Shadcn UI + Tailwind CSS + TypeScript              │
│                                                                  │
│  • Firebase SDK (Client Authentication)                         │
│  • React Query (State Management)                               │
│  • Axios (HTTP Client)                                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                  HTTPS / REST API (JWT Token)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Firebase Authentication                         │
│                    (Google Managed)                              │
│                                                                  │
│  ✅ User Sign Up / Sign In                                       │
│  ✅ Google OAuth                                                 │
│  ✅ Password Reset & Email Verification                          │
│  ✅ Token Generation & Management                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    Token Verification
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (Python)                       │
│                                                                  │
│  • Firebase Admin SDK (Token Verification)                      │
│  • SQLAlchemy ORM (Database Operations)                         │
│  • LangChain Agent (Conversational AI)                          │
│  • Background Scheduler (Pattern Analysis)                      │
│  • Pydantic Validation (Input/Output Schemas)                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                     SQLAlchemy ORM
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  PostgreSQL Database (Neon)                      │
│                                                                  │
│  📊 Tables:                                                      │
│     • users (profiles, preferences)                             │
│     • inventory (items, quantities, expiry)                     │
│     • consumption_log (usage patterns)                          │
│     • purchase_log (buy patterns)                               │
│     • shopping_prediction (AI predictions)                      │
│     • recipe_history (generated recipes)                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                      External API Calls
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      AI Services                                 │
│                                                                  │
│  🤖 Google Gemini 2.5 Flash-Lite                                │
│     • Recipe generation from inventory                          │
│     • Receipt/bill photo parsing (Vision)                       │
│     • Natural language processing                               │
│     • Conversational AI (via LangChain)                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    Webhook Integration
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              Messaging Bot Layer (Optional)                      │
│                                                                  │
│  📱 Telegram Bot                                                 │
│     • Natural language commands                                 │
│     • Photo-based inventory addition                            │
│     • Shopping list queries                                     │
│     • Recipe suggestions via chat                               │
│                                                                  │
│  💬 WhatsApp Bot (Future)                                        │
│     • WhatsApp Business API integration                         │
│     • Multi-user household support                              │
│     • Voice message support                                     │
│     • Group chat for family coordination                        │
└─────────────────────────────────────────────────────────────────┘
```

### Authentication Flow

**Firebase handles ALL user authentication:**
- ✅ No password storage in our database
- ✅ No session management needed
- ✅ Built-in OAuth providers (Google, etc.)
- ✅ Email verification & password reset out of the box
- ✅ Multi-device session management

**Our backend only:**
- Verifies Firebase ID tokens
- Extracts `firebase_uid` from tokens
- Uses `firebase_uid` as the primary user identifier

---

## 🛠️ Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) 0.115.0 (Python 3.11+)
- **Database**: [PostgreSQL](https://www.postgresql.org/) via [Neon](https://neon.tech) (Serverless)
- **ORM**: [SQLAlchemy](https://www.sqlalchemy.org/) 2.0.36
- **Authentication**: [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup) 6.5.0
- **AI/ML**: 
  - [Google Generative AI](https://ai.google.dev/) 1.0.0 (Gemini 2.5 Flash)
  - [LangChain](https://python.langchain.com/) 0.3.13
  - [LangGraph](https://langchain-ai.github.io/langgraph/) 0.2.59
- **Image Processing**: [Pillow](https://python-pillow.org/) 10.4.0
- **Validation**: [Pydantic](https://docs.pydantic.dev/) 2.9.2
- **Task Scheduling**: [APScheduler](https://apscheduler.readthedocs.io/) 3.10.4
- **Testing**: [Pytest](https://pytest.org/) 8.3.3

### Frontend
- **Framework**: [React](https://reactjs.org/) 18+ with [TypeScript](https://www.typescriptlang.org/)
- **Build Tool**: [Vite](https://vitejs.dev/)
- **UI Components**: [Shadcn UI](https://ui.shadcn.com/) + [Radix UI](https://www.radix-ui.com/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **State Management**: [@tanstack/react-query](https://tanstack.com/query) 5.90.2
- **HTTP Client**: [Axios](https://axios-http.com/) 1.12.2
- **Authentication**: [Firebase SDK](https://firebase.google.com/docs/web/setup) 12.3.0
- **Form Handling**: [React Hook Form](https://react-hook-form.com/)
- **Date Utilities**: [date-fns](https://date-fns.org/)

### DevOps & Tools
- **Version Control**: Git & GitHub
- **API Documentation**: Swagger UI (auto-generated by FastAPI)
- **Environment**: Python dotenv, Vite environment variables

---

## 🎯 Getting Started

### Prerequisites

- **Python** 3.11 or higher
- **Node.js** 18+ and npm/yarn/bun
- **PostgreSQL** database (or Neon account)
- **Firebase** project
- **Google AI Studio** API key (Gemini)

### API Keys Setup

#### 1. Firebase Authentication

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create a new project (e.g., "Kleio-AI")
3. Enable Authentication → Sign-in methods:
   - ✅ Google
   - ✅ Email/Password
4. **Download Service Account Key**:
   - Project Settings → Service Accounts
   - Click "Generate new private key"
   - Save as `backend/firebase-adminsdk.json`
5. **Get Web App Config** (for frontend):
   - Project Settings → General → Your apps
   - Copy the config object

#### 2. Google AI Studio (Gemini API)

1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Click "Get API Key"
3. Create a new key or use an existing project
4. Copy the API key

#### 3. PostgreSQL Database (Neon)

1. Go to [Neon](https://neon.tech)
2. Sign up with GitHub
3. Create a new project (e.g., "kleio-db")
4. Copy the connection string (starts with `postgresql://`)

---

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# Windows (CMD)
venv\Scripts\activate.bat
# Mac/Linux
source venv/bin/activate

# Install uv (faster pip alternative - optional)
pip install uv

# Install dependencies
# Using uv (faster)
uv pip install -r requirements.txt
# Or using pip
pip install -r requirements.txt
```

#### Create `.env` File

Create a `.env` file in the `backend/` directory:

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/kleio_db

# Firebase
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_PATH=./firebase-adminsdk.json

# Google AI
GEMINI_API_KEY=your_gemini_api_key_here

# App Settings
ENVIRONMENT=development
DEBUG=True
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Optional: Telegram Bot (for future use)
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=

```

#### Initialize Database

```bash
# Run database migrations
alembic upgrade head

# Or initialize manually (if needed)
python -c "from database import init_db; init_db()"
```

#### Run Backend Server

```bash
# Development mode (with auto-reload)
uvicorn main:app --reload --port 8000

# Or using Python directly
python main.py
```

The API will be available at:
- **API Base**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
# Or using yarn
yarn install
# Or using bun
bun install
```

#### Create `.env` File

Create a `.env` file in the `frontend/` directory:

```env
# Backend API
VITE_API_URL=http://localhost:8000

# Firebase Configuration
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

#### Run Frontend Development Server

```bash
# Start development server
npm run dev
# Or
yarn dev
# Or
bun dev
```

The app will be available at: http://localhost:8080

---

## 📁 Project Structure

```
kleio/
├── backend/                      # FastAPI backend
│   ├── agent/                    # LangChain AI agent
│   │   ├── __init__.py
│   │   ├── langchain_agent.py   # Conversational AI implementation
│   │   └── tools/               # Custom LangChain tools
│   ├── crud/                     # Database CRUD operations
│   │   ├── inventory.py         # Inventory operations
│   │   ├── user.py              # User operations
│   │   ├── purchase_log.py      # Purchase tracking
│   │   ├── pattern_analysis.py  # Pattern recognition
│   │   └── ...
│   ├── docs/                     # Backend documentation
│   │   ├── ARCHITECTURE.md      # Architecture details
│   │   ├── API_ENDPOINTS.md     # API reference
│   │   ├── AI_FEATURES.md       # AI features guide
│   │   ├── DATABASE_SCHEMA.md   # Database schema
│   │   ├── LANGCHAIN_AGENT.md   # Agent documentation
│   │   └── PATTERN_RECOGNITION.md
│   ├── migrations/               # Alembic database migrations
│   ├── models/                   # SQLAlchemy models
│   │   ├── user.py              # User model
│   │   ├── inventory.py         # Inventory model
│   │   ├── consumption_log.py   # Consumption tracking
│   │   ├── purchase_log.py      # Purchase tracking
│   │   ├── shopping_prediction.py
│   │   └── ...
│   ├── routers/                  # FastAPI routers (endpoints)
│   │   ├── users.py             # User endpoints
│   │   ├── inventory.py         # Inventory endpoints
│   │   ├── ai.py                # AI features endpoints
│   │   ├── recipes.py           # Recipe endpoints
│   │   ├── shopping.py          # Shopping list endpoints
│   │   ├── chat.py              # Conversational AI endpoints
│   │   └── health.py            # Health check
│   ├── schemas/                  # Pydantic schemas
│   │   ├── user.py              # User schemas
│   │   ├── inventory.py         # Inventory schemas
│   │   ├── ai.py                # AI request/response schemas
│   │   └── ...
│   ├── scripts/                  # Utility scripts
│   │   ├── test_ai_features.py  # Test AI endpoints
│   │   ├── test_langchain_agent.py
│   │   ├── seed_synthetic_data.py
│   │   └── ...
│   ├── tests/                    # Pytest test suite
│   │   ├── conftest.py
│   │   └── ...
│   ├── utils/                    # Utility functions
│   │   ├── auth.py              # Firebase token verification
│   │   ├── scheduler.py         # Background tasks
│   │   └── ...
│   ├── config.py                 # Configuration management
│   ├── database.py               # Database connection
│   ├── main.py                   # FastAPI application
│   ├── requirements.txt          # Python dependencies
│   ├── firebase-adminsdk.json   # Firebase service account (DO NOT COMMIT)
│   ├── .env                      # Environment variables (DO NOT COMMIT)
│   └── README.md                 # Backend README
│
├── frontend/                     # React frontend
│   ├── public/                   # Static assets
│   ├── src/
│   │   ├── assets/              # Images, fonts, etc.
│   │   ├── components/          # Reusable React components
│   │   │   ├── ui/             # Shadcn UI components
│   │   │   ├── dashboard/      # Dashboard-specific components
│   │   │   ├── inventory/      # Inventory components
│   │   │   ├── recipes/        # Recipe components
│   │   │   └── ...
│   │   ├── contexts/            # React contexts
│   │   │   └── AuthContext.tsx # Firebase auth context
│   │   ├── hooks/               # Custom React hooks
│   │   ├── lib/                 # Utility libraries
│   │   │   ├── api.ts          # Axios API client
│   │   │   └── firebase.ts     # Firebase config
│   │   ├── pages/               # Page components
│   │   │   ├── Index.tsx       # Landing page
│   │   │   ├── Login.tsx       # Login page
│   │   │   ├── Signup.tsx      # Signup page
│   │   │   ├── Onboarding.tsx  # User onboarding
│   │   │   ├── DashboardEnhanced.tsx
│   │   │   └── Settings.tsx
│   │   ├── App.tsx              # Main app component
│   │   ├── main.tsx             # Entry point
│   │   └── index.css            # Global styles
│   ├── .env                      # Environment variables (DO NOT COMMIT)
│   ├── package.json              # Node dependencies
│   ├── tsconfig.json             # TypeScript config
│   ├── vite.config.ts            # Vite config
│   ├── tailwind.config.ts        # Tailwind config
│   └── README.md                 # Frontend README
│
└── docs/                         # Project documentation
```

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000
```

### Authentication
All endpoints (except `/health`) require Firebase ID token:
```
Authorization: Bearer <firebase_id_token>
```

### Key Endpoints

#### Health & Status
- `GET /health` - Check API health
- `GET /health/db` - Check database connection

#### User Management
- `POST /api/users/profile` - Create/update user profile
- `GET /api/users/profile` - Get current user profile

#### Inventory Management
- `POST /api/inventory/add` - Add single item
- `POST /api/inventory/bulk-add` - Add multiple items
- `GET /api/inventory/list` - List all items (with filters)
- `GET /api/inventory/{item_id}` - Get specific item
- `PATCH /api/inventory/{item_id}/update` - Update item
- `DELETE /api/inventory/{item_id}` - Delete item
- `POST /api/inventory/{item_id}/mark-used` - Mark item as consumed

#### AI Features
- `POST /api/ai/parse-receipt` - Parse receipt photo (multipart/form-data)
- `POST /api/ai/confirm-receipt-items` - Confirm and add detected items
- `POST /api/ai/generate-recipe` - Generate recipe from inventory

#### Recipes
- `POST /api/recipes/generate` - Generate recipe
- `GET /api/recipes/history` - Get recipe history
- `POST /api/recipes/save` - Save recipe

#### Shopping Lists
- `GET /api/shopping/list` - Get smart shopping list
- `GET /api/shopping/analyze-patterns` - Analyze consumption patterns

#### Conversational AI
- `POST /api/chat/message` - Send message to AI assistant

### Interactive Documentation
Visit http://localhost:8000/docs for full interactive API documentation with request/response examples.

---

## 🤖 AI Features

### 1. Receipt/Bill Parsing (Gemini Vision)

**Upload a photo of your grocery bill**, and AI automatically extracts items:

```bash
curl -X POST http://localhost:8000/api/ai/parse-receipt \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@receipt.jpg"
```

**Response:**
```json
{
  "success": true,
  "items_detected": 3,
  "items": [
    {
      "name": "tomatoes",
      "quantity": 2.0,
      "unit": "kg",
      "category": "vegetables",
      "confidence": 0.95
    }
  ]
}
```

### 2. AI Recipe Generation (Gemini 2.5 Flash)

**Generate recipes from your available inventory**:

```bash
curl -X POST http://localhost:8000/api/recipes/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cooking_time_max": 30,
    "meal_type": "lunch",
    "cuisine_preference": "South Indian"
  }'
```

**Response:**
```json
{
  "recipe_name": "Tomato Rice",
  "ingredients": [...],
  "instructions": [...],
  "available_ingredients": 8,
  "missing_ingredients": 2,
  "cooking_time_minutes": 25
}
```

### 3. Conversational AI Assistant (LangChain + Gemini)

**Natural language interface**:

```bash
curl -X POST http://localhost:8000/api/chat/message \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I bought 2kg tomatoes and 1L milk today",
    "thread_id": "user123"
  }'
```

**Response:**
```json
{
  "response": "✅ I've added 2 items to your inventory:\n- Tomatoes (2.0 kg)\n- Milk (1.0 liter)\n\nIs there anything else you'd like to add?",
  "thread_id": "user123"
}
```

**Supported Queries:**
- "What's in my kitchen?"
- "What can I cook with what I have?"
- "Generate a shopping list"
- "I bought rice, dal, and onions"

---

## 🗄️ Database Schema

### Core Tables

#### `users`
```sql
- firebase_uid (PK)
- phone_number
- language_preference
- household_size
- location_city
- dietary_preferences (JSONB)
- created_at
```

#### `inventory`
```sql
- id (PK)
- firebase_uid (FK)
- item_name
- category
- quantity, unit
- added_date, expiry_date
- status (active/consumed/expired)
- photo_url
```

#### `consumption_log`
```sql
- id (PK)
- firebase_uid (FK)
- item_name, category
- quantity_consumed, unit
- consumed_date
- days_lasted
```

#### `purchase_log`
```sql
- id (PK)
- firebase_uid (FK)
- item_name, category
- quantity_purchased, unit
- purchase_date
- inventory_id (FK)
```

#### `shopping_prediction`
```sql
- id (PK)
- firebase_uid (FK)
- item_name, category
- avg_days_between_purchases
- avg_quantity_per_purchase
- avg_consumption_rate
- predicted_depletion_date
- suggested_quantity
- confidence_level, urgency
- data_points_count
- current_stock
```

#### `recipe_history`
```sql
- id (PK)
- firebase_uid (FK)
- recipe_name
- cuisine_type, meal_type
- ingredients (JSONB)
- instructions (TEXT)
- cooking_time_minutes
- generated_date
```

**See [backend/docs/DATABASE_SCHEMA.md](backend/docs/DATABASE_SCHEMA.md) for complete schema.**

---

## 💻 Development

#### Background Tasks
The application runs scheduled tasks for pattern analysis:
- **Pattern Analysis**: Runs daily at 6 AM
- **Expiry Checks**: Runs daily at 8 AM

### Frontend Development

#### Building for Production
```bash
cd frontend

# Build for production
npm run build

# Preview production build
npm run preview
```

#### Linting
```bash
# Run ESLint
npm run lint
```

---

### Manual API Testing

**Test Scripts:**
```bash
# Test AI features
python scripts/test_ai_features.py

# Test LangChain agent
python scripts/test_langchain_agent.py

# Test pattern recognition
python scripts/test_pattern_accuracy.py
```

**Using Postman:**
- Import collection: `backend/docs/postman_collection.json`
- Set environment variable: `FIREBASE_TOKEN`

---


### Interactive API Docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🎯 Roadmap

### ✅ Completed (MVP)
- [x] User authentication (Firebase)
- [x] Manual inventory management
- [x] Photo-based inventory (Gemini Vision)
- [x] AI recipe generation
- [x] Smart shopping lists
- [x] Pattern recognition system
- [x] Festival calendar
- [x] Conversational AI assistant (LangChain)
- [x] Dashboard UI with real-time stats

### 🚧 In Progress
- [ ] Telegram bot integration
- [ ] Mobile app (React Native)
- [ ] Enhanced analytics dashboard

### 🔮 Future Features (Post-MVP)
- [ ] WhatsApp bot integration
- [ ] Price tracking & comparison
- [ ] Local kirana store integration
- [ ] Meal planning calendar
- [ ] Nutritional analysis
- [ ] Community recipe sharing
- [ ] Maid/cook communication portal
- [ ] Multi-household management
- [ ] Voice assistant integration

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript strict mode for frontend
- Write tests for new features
- Update documentation as needed
- Keep commits atomic and well-described

---

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Authors

**Nithesh K**  
- Email: [mr.nithesh.k@gmail.com](mailto:mr.nithesh.k@gmail.com)
- GitHub: [@mrnithesh](https://github.com/mrnithesh)

---

## 🙏 Acknowledgments

- **Google Gemini** for powerful AI capabilities
- **Firebase** for seamless authentication
- **FastAPI** for excellent API framework
- **Shadcn UI** for beautiful React components
- **LangChain** for conversational AI framework
- **Neon** for serverless PostgreSQL

---

## 📞 Support

- **Documentation**: Check the `docs/` and `backend/docs/` folders
- **Issues**: [GitHub Issues](https://github.com/mrnithesh/kleio/issues)
- **Email**: mr.nithesh.k@gmail.com

---

## 🌟 Star History

If you find this project useful, please consider giving it a star! ⭐

---

<div align="center">
  <p>Made with ❤️ for Indian families</p>
  <p>© 2025 Kleio.ai - All Rights Reserved</p>
</div>
