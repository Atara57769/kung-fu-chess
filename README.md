# Kung-Fu Chess

A real-time, turn-less chess game with cooldowns, collision rules, and visual movement animations. The application is built using a Python backend utilizing WebSockets for real-time communication, and a desktop client rendering via OpenCV.

---

## ⚡ Game Mechanics & Rules

Unlike traditional chess, **Kung-Fu Chess** does not enforce turns. Both players can move their pieces simultaneously in real-time, subject to the following mechanics:

*   **Move Cooldowns:** After a piece finishes moving, it enters a cooldown phase during which it cannot be moved again.
    *   *Normal Move Cooldown:* **1500 ms**
*   **Airborne Jumps:** Players can command pieces to jump (specifically useful for Knights or dodging obstacles).
    *   *Jump Duration:* **1000 ms** (the piece is considered airborne)
    *   *Jump Cooldown:* **700 ms** (applied after landing)
*   **Airborne Capture:** Airborne pieces cannot be captured by normal ground moves. However, if an airborne piece is positioned on a cell when another piece arrives, or if it lands on an opponent's piece, captures are resolved dynamically based on their states.
*   **Real-time Collision:** Pieces travel dynamically across the board rather than teleporting. If two pieces collide mid-transit, collision rules determine which piece is captured or blocked.
*   **Pawn Promotion:** Pawns that successfully reach the opposite end of the board are automatically promoted to Queens.

---

## 🛠️ Technology Stack

*   **Language:** Python 3.10+
*   **Networking:** WebSockets (`websockets` library) for low-latency client-server synchronization.
*   **GUI & Rendering:** OpenCV (`cv2`) for window orchestration, sprite animation, scaling, and user event handling.
*   **Database:** SQLite (`sqlite3`) for user registration, authentication, and ELO rating persistence.
*   **Testing:** `pytest` for unit and integration tests, and a custom integration orchestrator (`test_runner.py`).

---

## 📂 Project Structure

```directory
├── client/                  # Desktop Game Client
│   ├── network/             # WebSocket connections and message dispatching
│   ├── services/            # Score tracking and helper utilities
│   └── ui/                  # OpenCV-based GUI
│       ├── animation/       # Sprite rendering, idle/move/jump state animations
│       ├── app/             # Matchmaking coordinators and terminal login
│       ├── assets/          # Sprites, boards, and graphic asset loaders
│       ├── board/           # Geometry mapping and coordinate calculations
│       └── rendering/       # OpenCV window drawing and image utilities
│
├── server/                  # Game Server
│   ├── database/            # SQLite tables for credentials and ELO storage
│   ├── game/                # Engine and rules controller
│   │   ├── engine/          # Physics tick loop, move arbiter, and controller
│   │   ├── rules/           # Legality checks, pawn promotion, win conditions
│   │   └── services/        # Board parser, printer, path collision, script runner
│   ├── matchmaking/         # ELO calculation mechanics
│   └── network/             # Server WebSocket connection manager
│
├── shared/                  # Shared Protocols & Data Models
│   ├── models/              # Game states, board snapshots, pieces, cells
│   ├── protocol/            # Message serialization/deserialization schemas
│   └── constants.py         # Global speeds, cooldown parameters, server ports
│
└── tests/                   # Extensive Test Suite
    ├── client/              # GUI and client network logic validation
    └── server/              # Rules, engine tick, and database verification
```

---

## 🚀 Getting Started

### 1. Prerequisites

Ensure you have Python 3.10+ installed. Install the required dependencies:

```bash
pip install opencv-python websockets pytest
```

### 2. Running the Server

Start the game server first. By default, it listens on `localhost:8765`:

```bash
python server_main.py --host localhost --port 8765
```

### 3. Running the Client

Start one or more client instances to play or observe:

```bash
python client_main.py --host localhost --port 8765 --scale 1.0
```

*   **Controls:**
    *   **Left Click:** Select a friendly piece, then left-click a destination cell to schedule a **normal move**.
    *   **Right Click:** Right-click on a piece to trigger an **airborne jump**.
*   **Onboarding:** If the username entered during login does not exist in the database, the server will auto-register the account with a starting rating of `1200`.

### 4. Running Simulations / Script Runners

You can execute pre-scripted gameplay matches or command-line pipelines using the core orchestration entry point:

```bash
python main.py
```

---

## 🧪 Testing

The codebase includes an extensive suite of unit and integration tests.

### Run pytest suite

Verify all components and network handlers:

```bash
pytest
```

### Run interactive script tests

Run terminal-based integration checks:

```bash
python test_runner.py
```
