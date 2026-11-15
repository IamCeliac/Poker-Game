Markdown
# Multiplayer Poker Game

A multi-user client-server poker application built in Python using TCP sockets, multithreading, SQLite persistence, and a Tkinter graphical interface.

## Features

* **User Authentication & Profiles:** Account registration, login/logout state tracking, and password management backed by SQLite.
* **Lobby & Table Management:** Create custom poker rooms, view active tables, join open games, and delete creator-owned tables (with automatic cleanup of empty rooms).
* **Concurrent Client-Server Architecture:** Multi-threaded TCP socket server handling simultaneous player connections and synchronized game state transitions.
* **Desktop GUI:** Interactive Tkinter client (`app.py`) for lobby navigation and gameplay.

## Project Structure

```text
Poker/
├── server.py         # Multi-threaded TCP server managing connections, lobbies, and game loops
├── app.py            # Tkinter GUI client entry point
├── database/         # SQLite database wrapper and schema initialization
├── game_files/       # Core poker logic, table state, and player/round management
├── user_files/       # User account handling and authentication logic
└── test_Files/       # Standalone test scripts for socket and game components
Prerequisites
Python 3.10 or higher

Standard library modules (socket, threading, sqlite3, tkinter) — no external third-party packages required.

Getting Started
Clone the repository:

Bash
git clone [https://github.com/IamCeliac/Poker-Game.git](https://github.com/IamCeliac/Poker-Game.git)
cd Poker-Game
Start the server:
Open a terminal in the project root and run:

Bash
python server.py
(The SQLite database file will be created automatically on first run if it does not already exist.)

Launch one or more clients:
Open a separate terminal for each player and run:

Bash
python app.py
Configuration
Server Host & Port: Check the top of server.py and app.py to adjust the IP address and port if running across different machines on a local network (defaults to 127.0.0.1 for local testing).

