# Kung-Fu Chess

A real-time, turn-less chess game featuring individual piece move cooldowns, continuous physical movement, airborne jumps, dynamic mid-air collisions, and real-time path interception. Built with Python, OpenCV for client rendering, and supporting both a lightweight direct WebSocket server and a full cloud-native microservices backend.

---

## ⚡ Game Mechanics & Rules

Unlike traditional turn-based chess, **Kung-Fu Chess** operates in continuous real-time. Both players command their pieces simultaneously subject to physics and cooldown constraints:

*   **Move Cooldowns:** Upon completing a move, a piece enters a cooldown state (**1500 ms** by default) before it can move again.
*   **Airborne Jumps:** Pieces can perform jump maneuvers (e.g. Knights jumping over obstacles or dodging incoming pieces).
    *   *Jump Duration:* **1000 ms** (the piece is airborne and evades ground captures)
    *   *Jump Cooldown:* **700 ms** (applied after landing)
*   **Airborne Capture & Resolution:** Airborne pieces cannot be captured by ground moves while in mid-air. Overlapping landings or arrival at the same cell are resolved dynamically based on state and position.
*   **Real-time Collision Detection:** Pieces travel continuously across the board geometry. Mid-transit collisions are arbitrated by the authoritative `GameEngine`.
*   **Pawn Promotion:** Pawns reaching the opponent's back rank are automatically promoted to Queens.

---

## 🛠️ Technology Stack & Architecture

Kung-Fu Chess offers dual execution modes depending on your deployment scale:

*   **Language & Core Logic:** Python 3.10+
*   **Client GUI & Rendering:** OpenCV (`cv2`), `numpy`, custom asset loaders, and animation managers.
*   **Standalone / Monolithic Mode:**
    *   **Networking:** Asynchronous WebSockets (`websockets`).
    *   **Database:** SQLite (`sqlite3`) with `bcrypt` password hashing for user credentials and ELO persistence.
*   **Distributed Microservices Mode:**
    *   **API Gateway:** FastAPI & Uvicorn for RESTful auth, registration, and user profiles.
    *   **Message Bus:** NATS JetStream (`nats-py`) for high-throughput inter-service messaging.
    *   **Caching & State:** Redis (`redis`) for session management, queue states, and fast lookups.
    *   **Persistence:** PostgreSQL (`psycopg2`, SQLAlchemy) for durable game history and user stats.
    *   **Containerization:** Docker & Docker Compose orchestrating 7 microservices.
*   **Testing & Diagnostics:** `pytest`, `pytest-cov`, and headless command script execution (`main.py`).

---

## 📂 Project Structure

```directory
├── client/                      # Desktop Game Client
│   ├── network/                 # Standalone & Distributed WS Client Adapters
│   ├── services/                # Score tracking, sound, and client utilities
│   └── ui/                      # OpenCV GUI System
│       ├── animation/           # Sprite rendering, idle/move/jump animations
│       ├── app/                 # Matchmaking coordinators and terminal onboarding
│       ├── assets/              # Sprites, chessboards, and asset loaders
│       ├── board/               # Geometry mapping and pixel/cell transformations
│       ├── history/             # Game move history tracker
│       ├── rendering/           # OpenCV window drawing pipeline & HUD
│       └── screens/             # UI screen states (Login, Matchmaking, Game Board)
│
├── server/                      # Monolithic Game Server Engine
│   ├── database/                # SQLite user table & ELO storage
│   ├── game/                    # Core Game Engine & Rules Controller
│   │   ├── engine/              # Physics tick loop, move arbiter, tick manager
│   │   ├── rules/               # Move legality, pawn promotion, win conditions
│   │   └── services/            # Board parser, path collision validator, script runner
│   ├── matchmaking/             # Monolithic ELO queue system
│   └── network/                 # Server WebSocket connection manager
│
├── services/                    # Cloud-Native Microservices Architecture
│   ├── api_gateway/             # FastAPI REST endpoints for Auth, Profile, & Stats (Port 8000)
│   ├── websocket_gateway/       # WS Gateway routing live client traffic to NATS (Port 8001)
│   ├── matchmaking_service/     # Distributed Redis/NATS matchmaking queue engine
│   ├── game_allocator/          # Room assignment & shard cluster scheduler
│   ├── game_server/             # Authoritative microservice GameEngine shard
│   ├── game_persistence_service/# Asynchronous PostgreSQL match history writer
│   └── observability_service/   # Prometheus/Health-check metrics exporter (Port 8002)
│
├── shared/                      # Shared Data Models & Protocols
│   ├── models/                  # Game state, board snapshots, pieces, cells
│   ├── protocol/                # JSON message schemas & serialization
│   └── constants.py             # Physics timings, ports, speeds, cooldown parameters
│
├── certs/                       # TLS/SSL Certificates for Secure WebSockets
├── tests/                       # Unit and Integration Test Suite
│   ├── client/                  # Client UI & networking unit tests
│   └── server/                  # Rules, tick loop, and microservices tests
│
├── client_main.py               # Entry point for Standalone Desktop Client
├── server_main.py               # Entry point for Standalone Monolithic Server
├── distributed_client_main.py   # Entry point for Distributed Microservices Client
├── docker-compose.yml           # Microservices stack orchestration
├── Dockerfile                   # Service base container image definition
├── Server_Design.md             # Comprehensive High-Scale Architectural Document
└── main.py                      # Simulation runner & headless script launcher
```

---

## 🚀 Getting Started

### 1. Prerequisites & Installation

Ensure **Python 3.10+** is installed on your system. Install required dependencies:

```bash
pip install -r requirements.txt
```

---

### Option A: Standalone / Monolithic Mode (Simple)

Run a local server with SQLite persistence and connect using the standalone client.

#### Step 1: Launch Server
By default, listens on `localhost:8765`:

```bash
python server_main.py --host localhost --port 8765
```

#### Step 2: Launch Client(s)
Open one or two client instances to play:

```bash
python client_main.py --host localhost --port 8765 --scale 1.0
```

---

### Option B: Distributed Microservices Mode (High-Scale)

Run the full microservices stack (API Gateway, WS Gateway, NATS, Redis, Postgres, Game Shards) via Docker Compose.

#### Step 1: Start Microservices Stack
```bash
docker-compose up --build
```

#### Step 2: Launch Distributed Client
Connect through the API & WebSocket Gateways:

```bash
python distributed_client_main.py --api-host http://localhost:8000 --ws-host localhost --ws-port 8001
```

*Distributed Client Options:*
* `--api-host`: REST API Gateway URL (default: `http://localhost:8000`)
* `--ws-host`: WebSocket Gateway Host (default: `localhost`)
* `--ws-port`: WebSocket Gateway Port (default: `8001`)
* `--no-ssl`: Disable SSL/TLS encryption for local development

---

## 🎮 Controls & Onboarding

*   **Player Onboarding:**
    *   Entering a new username during terminal login automatically registers the user account with an initial ELO rating of **1200**.
*   **Controls:**
    *   **Left Click:** Select a friendly piece, then left-click a destination square to schedule a **normal move**.
    *   **Right Click:** Right-click on a piece to trigger an **airborne jump**.

---

## 🌐 Microservices & Infrastructure Endpoints

| Service | Protocol | Host / Port | Description |
| :--- | :--- | :--- | :--- |
| **API Gateway** | REST (HTTP) | `http://localhost:8000` | User login, registration, user profiles, and room metadata |
| **WebSocket Gateway** | WebSocket | `ws://localhost:8001` | Live client connection & realtime game event streaming |
| **Observability Service** | REST (HTTP) | `http://localhost:8002` | Cluster metrics, health checks, and service monitoring |
| **NATS Message Bus** | TCP / HTTP | `4222` / `8222` | Distributed event bus & NATS management console |
| **Redis** | TCP | `6379` | In-memory session store & queue state cache |
| **PostgreSQL** | TCP | `5432` | Relational storage for user accounts & match histories |

---

## 🧪 Testing & Simulation

### Run pytest suite
Verify all game rules, server tick loop logic, and client components:

```bash
pytest
```

### Run coverage report
```bash
pytest --cov=server --cov=client --cov=shared --cov=services
```

### Run headless script simulation
Execute pre-scripted gameplay pipelines or command-line matches:

```bash
python main.py
```
