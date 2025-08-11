from loguru import logger
from ingest.watch import FileWatcher
from ingest.parser import parse_hand
from stats.calculator import StatsCalculator

def on_new_hand_text(hand_text: str):
    try:
        hand = parse_hand(hand_text)
        logger.debug(f"Parsed hand {hand.hand_id} at {hand.table_name}")
        # TODO: feed a StatsCalculator instance and later trigger HUD refresh
    except Exception as e:
        logger.exception(f"Failed to parse hand: {e}")

def main():
    logger.info("HeadsUp starting…")
    # TODO: read path from settings; for now, placeholder
    # watcher = FileWatcher(r'C:\Path\to\PokerStars\HandHistory\latest.txt', on_new_hand_text)
    # watcher.start()
    # watcher.join()
    logger.info("HeadsUp initialized (watcher disabled in scaffold).")
