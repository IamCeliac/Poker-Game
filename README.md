# ♠️ ♥️ Texas Hold'em Poker — Multiplayer Casino Arena (v1.0.1) ♣️ ♦️

A full-featured, multiplayer **Texas Hold'em Poker** desktop application built entirely in Python. The project features a custom 7-card poker engine, a multi-threaded TCP socket server, SQLite account and chip persistence, and an asynchronous Tkinter GUI that renders vector playing cards and a dynamic casino table without requiring external image assets.

---

## ✨ Key Features

### 🃏 Core Poker Engine
* **Full Street Progression:** Complete hand lifecycle across **Pre-Flop**, **Flop** (3 community cards), **Turn** (4th card), **River** (5th card), **Showdown**, and **Finished** states.
* **Pure-Python 7-Card Hand Evaluator:** Evaluates all $\binom{7}{5} = 21$ possible 5-card hands from each player's 2 hole cards and the 5 community cards. Accurately ranks hands from *High Card* (`0`) to *Straight Flush* (`8`), including Ace-low straights (`A-2-3-4-5`) and multi-kicker tiebreakers.
* **Rotating Dealer Button & Automatic Blinds:** Automatically posts the **Small Blind** ($\text{min\_bet} \div 2$) and **Big Blind** ($\text{min\_bet}$) at the start of every hand and rotates the dealer button across seated players between rounds.
* **Street-Level Betting Validation:** Tracks per-street player contributions (`currentStreetbet`) and action history (`playersActedThisStreet`) to validate **Fold**, **Check**, **Call**, **Bet**, **Raise To**, and **All-In** moves.
* **All-In Runouts & Split Pots:** Automatically deals out remaining community cards to Showdown when players are all-in, and splits the pot evenly (with odd-chip remainder distribution) in the event of a tie.
* **Table Stakes & Buy-In Enforcement:** Table hosts choose an even minimum bet between `$10` and `$1,000`. Players must hold at least $2 \times \text{min\_bet}$ chips to join a table or start a new hand.

### 🌐 Multiplayer Server & Networking
* **Multi-Threaded TCP Socket Server:** Handles concurrent player connections using dedicated client threads and newline-delimited JSON packets over TCP port `5555`.
* **Hole Card Privacy:** Broadcasts personalized game states (`get_state_for_player`) so each player sees their own hole cards while opponent cards remain masked as `"Hidden"` until Showdown.
* **Graceful Mid-Hand Disconnects:** Automatically folds any player who leaves a table or closes their window mid-hand (`handle_player_disconnect`), advancing the turn or awarding the pot to the last remaining player so tables never freeze.
* **Dynamic Lobby & Auto-Cleanup:** Supports up to 5 players per table, live lobby refreshes, and automatic deletion of empty tables when the last seated player leaves.

### 💾 User Accounts & SQLite Persistence
* **Authentication & Session Locks:** Account registration, login verification, and active session tracking (`isLoggedIn`) stored in SQLite (`database.db`), with automatic login lock resets on server boot.
* **Live Chip Persistence & Bankruptcy Refill:** New accounts start with `$500` chips. Balances are saved to SQLite after every hand and on logout. Players whose balance drops below `$100` can claim a free refill back to `$500` in the lobby.
* **Account Settings:** Supports live username changes (with automatic socket registry remapping), password updates, and permanent account deletion.

### 🖥️ Desktop GUI (`Tkinter` Canvas)
* **Non-Blocking Networking:** Uses a background socket listener thread paired with a thread-safe `queue.Queue` so real-time server broadcasts update the UI smoothly without freezing the window.
* **Vector Casino Table & Playing Cards:** Renders a wood-rimmed emerald felt poker table, community card slots, pot banners, and patterned playing cards directly on a `tk.Canvas`.
* **Hero-Centered Seat Rotation:** Dynamically rotates the 5 table seats so the logged-in player is always anchored at the bottom-center seat.
* **Dark & Light Themes:** Instant theme toggling across all portal, lobby, settings, and arena screens.

---

## 📁 Project Structure

```text
Poker/
├── app.py                   # Tkinter GUI client (Portal, Lobby, Settings, and Poker Table Arena)
├── server.py                # Multi-threaded TCP socket server and game state broadcaster
├── database.db              # Auto-generated SQLite database storing users and chip balances
├── database/
│   └── database.py          # SQLite schema initialization and login state reset utilities
├── user_files/
│   └── user.py              # User authentication, account management, and SQLite queries
├── game_files/
│   ├── card.py              # Card, CardSuit, and CardNumber enums and rank value helpers
│   ├── deck.py              # 52-card Deck generator, shuffler, and card drawing logic
│   ├── dealer.py            # Dealer management and 7-card Texas Hold'em hand evaluator
│   ├── player.py            # Player state, betting actions, table creation, and chip refills
│   ├── table.py             # Table management, buy-in checks, and dealer button tracking
│   ├── round.py             # Street progression, blinds, betting rules, and Showdown resolution
│   └── game.py              # Global open tables registry and game lifecycle helpers
└── test_Files/
    └── test_full_game.py    # Automated two-client socket simulation test script
```

---

## 🚀 Getting Started (Running from Source)

### Prerequisites
* **Python 3.10+** (with `tkinter` installed)
* No external `pip` packages are required to run the source code—everything uses Python's standard library (`tkinter`, `socket`, `threading`, `queue`, `json`, `sqlite3`).

### 1. Start the Server
Open a terminal in the project root directory and launch the server:

```bash
python server.py
```

You should see:
```text
[DATABASE] Database initialized and all logins reset.
[LISTENING] Poker Server is running on 0.0.0.0:5555...
```

### 2. Launch Player Clients
Open a new terminal window for each player you want to test and run:

```bash
python app.py
```

1. Click **Don't have an account? Sign Up** to create an account (starts with `$500` chips).
2. Sign in to enter the **Poker Lobby**.
3. Create a table with your desired **Min Bet** (`10`–`1000`, even number), or click **↻ Refresh** on a second client window to **Join** an existing table.
4. Once at least 2 players are seated, the table host can click **▶ Start Hand** in the top bar.

---

## 🌍 Playing Across Networks (LAN & Internet)

### 1. Host Configuration (`server.py`)
Ensure `server.py` binds to all network interfaces:
```python
SERVER_IP = '0.0.0.0'
SERVER_PORT = 5555
```

### 2. Firewall & Port Forwarding (For Internet Play)
* **Router:** Forward TCP port `5555` to the host PC's local IPv4 address.
* **Windows Firewall:** Open PowerShell as Administrator on the host PC and allow inbound TCP traffic on port `5555`:
  ```powershell
  New-NetFirewallRule -DisplayName "PokerServer TCP 5555" -Direction Inbound -LocalPort 5555 -Protocol TCP -Action Allow
  ```

### 3. Client Configuration (`app.py`)
At the top of `app.py`, set `SERVER_IP` to match how you are connecting:
* **Same PC as Server:** `SERVER_IP = "127.0.0.1"`
* **Same Wi-Fi / LAN:** `SERVER_IP = "192.168.x.x"` (the host PC's local IPv4 address)
* **Over the Internet:** `SERVER_IP = "<Host_Public_IPv4>"` (find via `curl ifconfig.me` on the host PC)

### 4. Running the Client on macOS
macOS users only need `app.py`. Install Python with Tkinter support and run the client from Terminal:
```bash
brew install python-tk
python3 app.py
```

---

## 📦 Building Standalone Executables (`PyInstaller`)

You can package the client and server into standalone executables so players do not need Python installed.

### 1. Install PyInstaller
```bash
pip install --upgrade pyinstaller
```

### 2. Build the GUI Client (`PokerClient.exe` / `PokerClient.app`)
* **Windows:**
  ```powershell
  pyinstaller --onefile --noconsole --name PokerClient app.py
  ```
* **macOS:**
  ```bash
  pyinstaller --onefile --windowed --name PokerClient app.py
  ```

### 3. Build the Server (`PokerServer.exe`)
```powershell
pyinstaller --onefile --name PokerServer --hidden-import=game_files.game --hidden-import=game_files.table --hidden-import=game_files.round --hidden-import=game_files.player --hidden-import=game_files.dealer --hidden-import=game_files.deck --hidden-import=game_files.card --hidden-import=user_files.user --hidden-import=database.database server.py
```

Compiled executables will appear inside the `dist/` folder.

---

## 🧪 Running Automated Socket Tests

With `server.py` running in one terminal, run the automated simulation script in a second terminal to verify account creation, blind posting, street progression, 7-card Showdown evaluation, and fold wins:

```bash
python -u test_Files/test_full_game.py
```