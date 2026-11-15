# Texas Hold'em Poker

A multiplayer Texas Hold'em client-server application written in Python. The project is built entirely with the Python standard library, combining a custom poker rule engine, a multi-threaded TCP socket server, SQLite persistence, and a Tkinter desktop client.

## Overview

The system is split into two primary components:
* **Server (`server.py`):** Manages client connections over TCP sockets using a thread-per-client model, coordinates table state and active rounds, enforces poker rules, and persists user accounts and chip balances to a local SQLite database (`database.db`).
* **Client (`app.py`):** Provides a Tkinter GUI with a dedicated background socket listener thread and a thread-safe message queue (`queue.Queue`) to process asynchronous server broadcasts without blocking the UI thread. The table and playing cards are drawn procedurally on a `tk.Canvas`.

## Features

* **Game Engine:** Supports full street progression (Pre-Flop, Flop, Turn, River, Showdown) for 2 to 5 players per table.
* **Hand Evaluation:** Evaluates all 21 five-card combinations from a player's 2 hole cards and the 5 community cards, supporting standard hand rankings, Ace-low straights, tiebreakers, and split pots.
* **Blinds & Betting:** Automatically posts Small Blind (`min_bet // 2`) and Big Blind (`min_bet`) bets, rotates the dealer button each round, and validates street-level betting actions (`check`, `call`, `bet`, `raise`, `all_in`, `fold`).
* **Table Buy-In Rules:** Table creators configure an even minimum bet between 10 and 1,000 chips. Players must hold a balance of at least `2 * min_bet` to join a table or start a hand.
* **State Synchronization & Card Privacy:** Broadcasts per-player JSON state updates where opponent hole cards remain masked until Showdown.
* **Disconnect Handling:** Automatically folds players who leave a table or disconnect mid-hand so active rounds do not stall, and cleans up empty tables when the last player exits.
* **Account & Balance Management:** Stores credentials, login session flags, and chip balances in SQLite. New accounts start with 500 chips, and players under 100 chips can reset their balance to 500 from the lobby.

## Project Structure

```text
Poker/
├── app.py                   # Tkinter GUI client and background network listener
├── server.py                # Multi-threaded TCP server and client request router
├── database.db              # SQLite database file (created automatically on server start)
├── database/
│   └── database.py          # Database schema setup and login reset queries
├── user_files/
│   └── user.py              # Account creation, authentication, and balance updates
├── game_files/
│   ├── card.py              # Card, CardSuit, and CardNumber definitions
│   ├── deck.py              # 52-card deck generation and shuffling
│   ├── dealer.py            # Community card dealing and 7-card hand evaluation
│   ├── player.py            # Player state, betting methods, and table actions
│   ├── table.py             # Table state, seat limits, and buy-in validation
│   ├── round.py             # Betting street state machine and Showdown resolution
│   └── game.py              # Open table registry
└── test_Files/
    └── test_full_game.py    # Automated two-client socket integration test
```

## Getting Started

### Prerequisites

* Python 3.10 or newer (with `tkinter` included)
* No third-party packages are required to run from source.

### Running the Server

From the project root directory, start the server:

```bash
python server.py
```

On startup, the server initializes `database.db`, resets any stale login flags, and listens on `0.0.0.0:5555`.

### Running the Client

Open a separate terminal for each client instance:

```bash
python app.py
```

1. Register a new account on the Sign Up screen (initialized with 500 chips).
2. Sign in to view the lobby.
3. Create a new table with an even minimum bet between 10 and 1,000, or click **Refresh** on another client to join an existing table.
4. Once at least 2 players have joined, the table creator can start the hand.

## Network Configuration

### Server Binding

In `server.py`, keep `SERVER_IP` bound to all interfaces:

```python
SERVER_IP = '0.0.0.0'
SERVER_PORT = 5555
```

### Client Connection Target

In `app.py`, set `SERVER_IP` to match your deployment environment:

* **Localhost (same machine):** `SERVER_IP = "127.0.0.1"`
* **LAN (same local network):** Set `SERVER_IP` to the host machine's local IPv4 address (e.g., `192.168.1.x`).
* **WAN (over the internet):** Forward TCP port `5555` on the host router, allow inbound TCP port `5555` through the host firewall, and set `SERVER_IP` in `app.py` to the host's public IPv4 address.

To allow inbound connections on Windows PowerShell (Run as Administrator):

```powershell
New-NetFirewallRule -DisplayName "PokerServer TCP 5555" -Direction Inbound -LocalPort 5555 -Protocol TCP -Action Allow
```

### Running on macOS

macOS clients only require `app.py`. Ensure Python is installed with Tcl/Tk support:

```bash
brew install python-tk
python3 app.py
```

## Building Executables

Standalone executables can be built with `PyInstaller`:

```bash
pip install --upgrade pyinstaller
```

### Client Executable

* **Windows:**
  ```powershell
  pyinstaller --onefile --noconsole --name PokerClient app.py
  ```
* **macOS:**
  ```bash
  pyinstaller --onefile --windowed --name PokerClient app.py
  ```

### Server Executable

```powershell
pyinstaller --onefile --name PokerServer --hidden-import=game_files.game --hidden-import=game_files.table --hidden-import=game_files.round --hidden-import=game_files.player --hidden-import=game_files.dealer --hidden-import=game_files.deck --hidden-import=game_files.card --hidden-import=user_files.user --hidden-import=database.database server.py
```

The compiled binaries are output to the `dist/` directory.

## Testing

To run the automated two-player socket test against a running server instance:

```bash
python -u test_Files/test_full_game.py
```