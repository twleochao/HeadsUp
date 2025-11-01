import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from PokerNow import PokerClient

# --- CONFIGURATION ---
# This tells Selenium to look for 'chromedriver.exe' in the *same folder*
# as this script.
DRIVER_PATH = os.path.join(os.getcwd(), "chromedriver.exe")
# ---------------------

try:
    # 1. Set up the Selenium "service"
    service = Service(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(service=service)

    # 2. Start the PokerClient
    client = PokerClient(driver)
    
    # 3. Open the game page
    client.navigate('https://www.pokernow.club/start-game')
    
    print("\n" + "="*30)
    print("ACTION REQUIRED:")
    print("1. In the Chrome window, start a new game.")
    print("2. Open the 'Invite' link in a new tab to join as a player.")
    print("3. Start the game (you may need a 3rd player to join).")
    print("="*30)
    input("\nPress Enter here when you are sitting at the table and the game has started...")
    
    print("\nSuccessfully connected to game. Fetching state every 3 seconds...")
    print("Press Ctrl+C to stop.")
    
    while True:
        game_state = client.get_game_state()
        
        print("\n--- NEW GAME STATE ---")
        print(f"Pot: {game_state.pot}")
        print(f"Board: {[f'{c.rank}{c.suit}' for c in game_state.community_cards]}")
        
        for player in game_state.players_info:
            if player.is_hero:
                print(f"  > HERO: {player.name}")
                print(f"    Cards: {[f'{c.rank}{c.suit}' for c in player.cards]}")
                print(f"    Stack: {player.stack_value}")
                print(f"    Bet: {player.bet_value}")
        
        print(f"Is it our turn? {client.is_your_turn()}")
        
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