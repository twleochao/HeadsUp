import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from PokerNow import PokerClient

DRIVER_PATH = os.path.join(os.getcwd(), "chromedriver.exe")

try:
    if not os.path.exists(DRIVER_PATH):
        print(f"Error: chromedriver.exe not found at {DRIVER_PATH}")
        print("Please download the matching version for your Chrome browser and place it in the project root.")
    else:
        service = Service(executable_path=DRIVER_PATH)
        driver = webdriver.Chrome(service=service)
        client = PokerClient(driver, cookie_path='pokernow_cookies.pkl')
        
        print("\n" + "="*30)
        game_link = input("Please paste a PokerNow spectator link to join: ")
        print("="*30)
        
        if "pokernow.club/games/" not in game_link:
            print("Invalid link. Must be a pokernow.club/games/...")
        else:
            client.navigate(game_link)
            print("Successfully navigated to game. Waiting for game to load...")
            time.sleep(5) # Give the page time to load
            
            print("\nFetching state every 3 seconds...")
            print("Press Ctrl+C to stop.")

            game_state = client.game_state_manager.get_game_state()
            
            while True:
                community_cards = game_state.get_community_cards()
                players = game_state.get_players_info()
                
                print("\n--- NEW GAME STATE ---")
                print(f"Board: {[f'{c.rank}{c.suit}' for c in community_cards]}")

                for player in players:
                    player_name = player.name or "Unknown"
                    is_hero_str = "(HERO)" if player.is_hero else ""
                    
                    print(f"  > Player: {player_name.ljust(20)} {is_hero_str}")
                    print(f"    Cards: {[f'{c.rank}{c.suit}' for c in player.cards]}")
                    print(f"    Stack: {player.stack_value}")
                    print(f"    Bet:   {player.bet_value}")

                print(f"Is it our turn? {game_state.is_your_turn()}")
                
                time.sleep(3)

except Exception as e:
    print(f"\nAn error occurred: {e}")
    if "This version of ChromeDriver" in str(e):
        print("\n*** FIX: Your 'chromedriver.exe' version does not match your")
        print("    Google Chrome browser version. Follow the steps to re-download.")
except KeyboardInterrupt:
    print("\nStopping test.")
finally:
    if 'driver' in locals():
        driver.quit()
    print("Test finished.")
