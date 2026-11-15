import socket
import threading
import json
from database.database import Database
from user_files.user import User
from game_files.game import Game
from game_files.round import RoundStage


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
                            "open_tables": [{"table_name": t.tableName, "creator": t.creator, "min_bet": t.min_bet }for t in Game.openTables]
                        })

                    

                    # --- GUARD: All actions below require being logged in first! ---
                    elif current_player is None:
                        raise ValueError("You must log in first.")
                    
                    elif action == "change_username":
                        current_username = data["current_username"]
                        new_username = data["new_username"]
                        current_player.ChangeUsername(current_username, new_username)

                        if current_username in connected_clients:
                            del connected_clients[current_username]
                        connected_clients[new_username] = client_socket

                        send_to_client(client_socket,{
                            "status": "ok",
                            "type": "change_username_success",
                            "username": current_player.username,
                            "balance": current_player.currentBalance
                        })
                        
                    elif action == "change_password":
                        current_password = data["current_password"]
                        new_password = data["new_password"]
                        current_player.ChangePassword(current_password, new_password)
                        send_to_client(client_socket,{
                            "status": "ok",
                            "type": "change_password_success",
                            "username": current_player.username,
                            "balance": current_player.currentBalance
                        })                   
                    

                # --- Delete User ---
                    elif action == "delete_user":
                        username_todelete = data["username"]
                        User.DeleteUser(username_todelete)
                        if current_player.username in connected_clients:
                            del connected_clients[current_player.username]
                        send_to_client(client_socket,{
                            "status": "ok",
                            "type": "deleteuser_success",
                            "username": current_player.username,
                            "balance": current_player.currentBalance
                        })
                        current_player = None
                    
                    # --- 3. CREATE TABLE ---
                    elif action == "create_table":
                        table_name = data["table_name"]
                        min_bet = int(data.get("min_bet",20))
                        if not current_player.isTableCreated:
                            current_player.CreateTable(table_name,min_bet)
                            current_player.isTableCreated = True
                        else:
                            raise ValueError("Player can only create one table.")
                        send_to_client(client_socket,{
                                "status": "ok",
                                "type": "table_joined",
                                "table_name": table_name,
                                "min_bet": min_bet,
                                "creator": current_player.username,
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

                    elif action == "leave_table":
                        table_name = current_player.currentTableName
                        if not table_name:
                            raise ValueError("You are not sitting at a table")
                        current_round = active_rounds.get(table_name)
                        if current_round is not None:
                            current_round.handle_player_disconnect(current_player)
                            broadcast_game_state(table_name, f"{current_player.username} left the table and folded.")
                            if current_round.roundStage == RoundStage.FINISHED:
                                del active_rounds[table_name]

                        current_player.ExitGame()
                        table = current_player.RemovePlayerFromTable()

                        send_to_client(client_socket,{
                            "status": "ok",
                            "type": "left_table",
                            "username": current_player.username,
                            "balance": current_player.currentBalance,
                            "open_tables": [
                                {"table_name": t.tableName, "creator": t.creator, "min_bet": t.min_bet}
                                for t in Game.openTables
                            ]
                        })

                        if table is not None and table in Game.openTables:
                            broadcast_to_table(table_name,{
                                "status": "ok",
                                "type": "player_left",
                                "table_name": table_name,
                                "players": [p.username for p in table.players]
                            })

                    elif action == "get_tables":
                        send_to_client(client_socket,{
                            "status": "ok",
                            "type": "get_tables_list",
                            "open_tables": [
                                {"table_name": t.tableName, "creator": t.creator, "min_bet": t.min_bet}
                                for t in Game.openTables
                            ]
                        })

                    # --- 5. DELETE TABLE ---
                    elif action == "delete_table":
                        table_name = data["table_name"]
                        table = Game.GetTableByName(table_name)
                        if table is None:
                            raise ValueError(f"Table '{table_name}' does not exist.")
                        current_player.DeleteTable()
                        send_to_client(client_socket,{
                            "status": "ok",
                            "type": "table_deleted",
                            "table_name": table_name
                        })

                    # --- 6. START ROUND ---
                    elif action == "start_round":
                        table_name = current_player.currentTableName
                        table = Game.GetTableByName(table_name)
                        if table is None:
                            raise ValueError("You are not sitting at a table.")

                        if table.creator != current_player.username:
                            raise ValueError("Only the table creator is allowd to start a round")

                        if table.tableName in active_rounds:
                            raise ValueError("A round is already in progress!")

                        game = Game()
                        new_round = game.start_game(table)
                        new_round.start_round()
                        active_rounds[table_name] = new_round

                        broadcast_game_state(table_name, "New round started!")

                    # --- 7. PLAYER GAME MOVE (bet, call, raise, fold, check) ---
                    elif action == "game_move":
                        table_name = current_player.currentTableName
                        current_round = active_rounds.get(table_name)
                        if current_round is None:
                            raise ValueError("No active round at your table.")

                        move = data["move"]          # "bet", "call", "raise", "fold", "check"
                        amount = data.get("amount", 0)

                        current_round.handle_player_action(current_player, move, amount)

                        action_text = f"{current_player.username} chose {move} ({amount})"
                        if current_round.roundStage == RoundStage.FINISHED and current_round.winner_message:
                            action_text += f" | {current_round.winner_message}"

                       
                        broadcast_game_state(table_name,action_text)

                        if current_round.roundStage == RoundStage.FINISHED:
                            del active_rounds[table_name]

                    elif action == "refill_balance":
                        new_balance = current_player.RefillBalance()
                        send_to_client(client_socket, {
                            "status": "ok",
                            "type": "refill_success",
                            "balance": new_balance,
                            "message": "Your balance has been refilled to 500 chips."
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
        # Cleanup when the loop breaks (player disconnects)
        if current_player is not None:
            table_name = current_player.currentTableName
            if table_name:
                current_round = active_rounds.get(table_name)
                if current_round is not None:
                    current_round.handle_player_disconnect(current_player)
                    broadcast_game_state(table_name, f"{current_player.username} disconnected and folded.")
                    if current_round.roundStage == RoundStage.FINISHED:
                        del active_rounds[table_name]

                current_player.RemovePlayerFromTable()
                broadcast_to_table(table_name, {
                    "status": "ok",
                    "type": "player_left",
                    "table_name": table_name,
                    "players": [p.username for p in Game.GetTableByName(table_name).players]
                } if Game.GetTableByName(table_name) else {})

            User.LogOutUser(current_player)
            if current_player.username in connected_clients:
                del connected_clients[current_player.username]
            print(f"[LOGOUT] {current_player.username} logged out and balance saved.")

        client_socket.close()
        print(f"[CLOSED] Connection with {client_address} closed.")

def send_to_client(client_socket, payload_dict):
    """Sends a JSON dictionary to a single client."""
    try:
        message = json.dumps(payload_dict) + "\n"
        client_socket.send(message.encode("utf-8"))
    except (ConnectionResetError,ConnectionAbortedError,BrokenPipeError):
        pass

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

def broadcast_game_state(table_name, last_action_text=""):
    """Sends each player at the table their personalized game state (with their own cards visible)."""
    current_round = active_rounds.get(table_name)
    if current_round is None:
        return

    for player in current_round.active_players:
        if player.username in connected_clients:
            player_socket = connected_clients[player.username]
            state_payload = current_round.get_state_for_player(player)
            state_payload["last_action"] = last_action_text
            send_to_client(player_socket, state_payload)

    

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