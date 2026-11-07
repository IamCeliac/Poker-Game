import socket
import threading
import json
from database.database import Database
from user_files.user import User
from game_files.game import Game

SERVER_IP = '127.0.0.1'
SERVER_PORT = 5555

connected_clients = {} # Format {"username": client_socket}
active_rounds = {} # Format: {"table_name": Round_Stage}


def handle_client(client_socket,client_address):
    """Runs a seperate thread for each connected player 
    and listens for messages from this specific player until they disconnect"""

    print(f"[NEW CONNECTION] {client_address} connected.")
    current_player = None # waiting until player logs in

    try:
        while True:
            raw_data = client_socket.recv(4096)

            # if recv() returns mpty bytes
            if not raw_data:
                break

            for line in raw_data.decode("utf-8").strip().split("\n"):
                if not line:
                    continue

                data = json.loads(line)
                action = data.get("action")
                print(f"[ACTION from {client_address}] {data}")

                # inner try to catch ValueErrors caused by use,player,table or round
                try:
                    # --- 1. SIGN UP ---
                    if action == "signup":
                        u = User(data["username"],data["password"])
                        u.CreateNewUser()
                        send_to_client(client_socket,{
                            "status":"ok",
                            "type": "signup_success",
                            "message": "Account created, you may log in."
                        })

                    # --- 2. SIGN IN ---
                    elif action == "signin":
                        u = User(data["username"], data["password"])
                        current_player = u.LogIntoUser()  # Returns Player instance!
                        connected_clients[current_player.username] = client_socket

                        send_to_client(client_socket,{
                            "status": "ok",
                            "type": "signin_success",
                            "username": current_player.username,
                            "balance": current_player.currentBalance,
                            "open_tables": [t.tableName for t in Game.openTables]
                        })

                    # --- GUARD: All actions below require being logged in first! ---
                    elif current_player is None:
                        raise ValueError("You must log in first.")
                    # --- 3. CREATE TABLE ---
                    elif action == "create_table":
                        table_name = data["table_name"]
                        current_player.CreateTable(table_name)
                        send_to_client(client_socket,{
                            "status": "ok",
                            "type": "table_joined",
                            "table_name": table_name,
                            "players": [current_player.username]
                        })

                    # --- 4. JOIN EXISTING TABLE ---
                    elif action == "join_table":
                        table_name = data["table_name"]
                        table = Game.GetTableByName(table_name)
                        if table is None:
                            raise ValueError(f"Table '{table_name}' does not exist.")
                        
                        table.add_player(current_player)
                        current_player.currentTableName = table_name

                        broadcast_to_table(table_name,{
                            "status": "ok",
                            "type": "player_joined",
                            "table_name": table_name,
                            "players": [p.username for p in table.players]
                        })


                    # --- 5. START ROUND ---
                    elif action == "start_round":
                        table_name = current_player.currentTableName
                        table = Game.GetTableByName(table_name)
                        if table is None:
                            raise ValueError("You are not sitting at a table.")

                        game = Game()
                        new_round = game.start_game(table)
                        new_round.start_round()
                        active_rounds[table_name] = new_round

                        broadcast_to_table(table_name, {
                            "status": "ok",
                            "type": "round_started",
                            "pot": new_round.pot,
                            "stage": new_round.roundStage.value,
                            "current_turn": new_round.get_current_player().username
                        })

                    # --- 6. PLAYER GAME MOVE (bet, call, raise, fold, check) ---
                    elif action == "game_move":
                        table_name = current_player.currentTableName
                        current_round = active_rounds.get(table_name)
                        if current_round is None:
                            raise ValueError("No active round at your table.")

                        move = data["move"]          # "bet", "call", "raise", "fold", "check"
                        amount = data.get("amount", 0)

                        # Runs your exact turn logic from round.py!
                        current_round.handle_player_action(current_player, move, amount)

                        # Tell everyone at the table what happened and whose turn is next
                        broadcast_to_table(table_name, {
                            "status": "ok",
                            "type": "table_update",
                            "last_Action": f"{current_player.username} chose {move} ({amount})",
                            "pot": current_round.pot,
                            "stage": current_round.roundStage.value,
                            "current_turn": current_round.get_current_player().username
                        })

                    else:
                        raise ValueError(f"Unknown action: {action}")

                except ValueError as ve:
                    send_to_client(client_socket, {
                        "status": "error",
                        "message": str(ve)
                    })

    except ConnectionResetError:
        print(f"[DISCONNECTED] {client_address} forcefully closed the window.")
    except Exception as e:
        print(f"[ERROR] {client_address}: {e}")
    finally:
        # 3. Cleanup when the loop breaks (player disconnects)
        if current_player is not None:
            if current_player.currentTableName:
                current_player.RemovePlayerFromTable()
            User.LogOutUser(current_player)
            if current_player.username in connected_clients:
                del connected_clients[current_player.username]
            print(f"[LOGOUT] {current_player.username} logged out and balance saved.")

        client_socket.close()
        print(f"[CLOSED] Connection with {client_address} closed.")

def send_to_client(client_socket, payload_dict):
    """Sends a JSON dictionary to a single client."""
    message = json.dumps(payload_dict) + "\n"
    client_socket.send(message.encode("utf-8"))

def broadcast_to_table(table_name, payload_dict):
    """Sends a JSON dictionary to EVERY player currently sitting at a specific table."""
    table = Game.GetTableByName(table_name)
    if table is None:
        return

    for player in table.players:
        # Find each seated player's socket in connected_clients and send the update
        if player.username in connected_clients:
            player_socket = connected_clients[player.username]
            send_to_client(player_socket, payload_dict)

def start_server():
    """Main function that boots the database and listens for connections """

    db = Database('database.db')
    db.create_table()
    db.reset_all_logins()
    print("[DATABASE] Database initialized and all logins reset.")

    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

    server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

    server_socket.bind((SERVER_IP,SERVER_PORT))
    server_socket.listen()
    print(f"[LISTENING] Poker Server is running on {SERVER_IP}:{SERVER_PORT}...")

    while True:
        client_socket,client_address = server_socket.accept()

        client_thread = threading.Thread(
            target = handle_client,
            args=(client_socket,client_address),
            daemon=True
        )
        client_thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    start_server()