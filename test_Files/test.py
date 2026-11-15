import socket
import json
import time

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5555


class MockClient:
    def __init__(self, name):
        self.name = name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((SERVER_IP, SERVER_PORT))
        self.sock.settimeout(2.0)
        self.last_state = None

    def send(self, payload):
        msg = json.dumps(payload) + "\n"
        self.sock.sendall(msg.encode("utf-8"))
        time.sleep(0.15)
        self.read_available()

    def read_available(self):
        try:
            while True:
                data = self.sock.recv(4096).decode("utf-8")
                if not data:
                    break
                for line in data.strip().split("\n"):
                    if not line:
                        continue
                    parsed = json.loads(line)
                    if parsed.get("type") == "game_state":
                        self.last_state = parsed
                    print(f"[{self.name} RECEIVED] {parsed}")
        except socket.timeout:
            pass

    def close(self):
        self.sock.close()


def get_active_client(c1, c2):
    c1.read_available()
    c2.read_available()
    turn_user = c1.last_state.get("current_turn")
    return c1 if turn_user == "test_p1" else c2


def run_simulation():
    p1 = MockClient("P1")
    p2 = MockClient("P2")

    print("\n--- 1. SIGN UP & SIGN IN ---")
    p1.send({"action": "signup", "username": "test_p1", "password": "123"})
    p2.send({"action": "signup", "username": "test_p2", "password": "123"})

    p1.send({"action": "signin", "username": "test_p1", "password": "123"})
    p2.send({"action": "signin", "username": "test_p2", "password": "123"})

    print("\n--- 2. CREATE & JOIN TABLE (min_bet = 20) ---")
    p1.send({"action": "create_table", "table_name": "HighRollers", "min_bet": 20})
    p2.send({"action": "join_table", "table_name": "HighRollers"})

    print("\n--- 3. START ROUND 1 (Play to Showdown) ---")
    p1.send({"action": "start_round"})

    # Pre-Flop: Small blind owes 10 to call, Big blind checks
    active = get_active_client(p1, p2)
    active.send({"action": "game_move", "move": "call"})
    active = get_active_client(p1, p2)
    active.send({"action": "game_move", "move": "check"})

    # Flop, Turn, River: Both players check through each street
    for street in ["Flop", "Turn", "River"]:
        print(f"\n--- Street: {street} ---")
        active = get_active_client(p1, p2)
        active.send({"action": "game_move", "move": "check"})
        active = get_active_client(p1, p2)
        active.send({"action": "game_move", "move": "check"})

    p1.read_available()
    p2.read_available()
    print(f"\n[ROUND 1 END STATE] Stage: {p1.last_state['stage']} | Pot: {p1.last_state['pot']} | Cards: {p1.last_state['community_cards']}")
    print(f"[ROUND 1 PLAYERS] {p1.last_state['players']}")

    print("\n--- 4. START ROUND 2 (Test Fold Win & Dealer Reset) ---")
    p1.send({"action": "start_round"})

    active = get_active_client(p1, p2)
    active.send({"action": "game_move", "move": "fold"})

    p1.read_available()
    p2.read_available()


if __name__ == "__main__":
    print("Starting simulation...", flush=True)
    run_simulation()

