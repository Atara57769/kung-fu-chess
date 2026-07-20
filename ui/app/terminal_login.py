import sys
import time
from network.client import GameClient

def run_terminal_login(client: GameClient) -> None:
    """Prompts for user credentials in terminal and authenticates with WebSocket server."""
    print("\n==============================")
    print("    KUNG-FU CHESS ONLINE LOGIN  ")
    print("==============================\n")
    
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    if not username or not password:
        print("Error: Username and Password cannot be empty.")
        sys.exit(1)
        
    client.authenticate(username, password)
    
    start_t = time.time()
    while not client.authenticated and not client.error_message:
        time.sleep(0.1)
        if time.time() - start_t > 5.0:
            print("Authentication timeout. Could not reach server.")
            client.stop()
            sys.exit(1)
            
    if client.error_message:
        print(f"Authentication failed: {client.error_message}")
        client.stop()
        sys.exit(1)
        
    print(f"Authentication success! Welcome {client.username} (ELO: {client.rating})")
