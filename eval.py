import pandas as pd
import glob
import os
import argparse

LOG_DIR = "data/logs"

def analyze_session(log_file: str):
    print(f"\n--- Analyzing Session: {os.path.basename(log_file)} ---")
    
    try:
        df = pd.read_csv(log_file)
        if df.empty:
            print("  No data in this session.")
            return
    except FileNotFoundError:
        print(f"  Error: Log file not found at {log_file}")
        return

    df = df[df['hero_action'] != 'UNKNOWN'].copy()
    if df.empty:
        print("  No completed actions were logged.")
        return
    print("\n[GTO Deviation Report]")
    
    df['is_deviant'] = df['hero_action'].str.upper() != df['gto_action'].str.upper()
    
    call_leaks = df[
        (df['hero_action'] == 'CALL') & 
        (df['gto_action'] == 'RAISE')
    ]
    print(f"\n  Called when GTO was to Raise: {len(call_leaks)} time(s)")
    if not call_leaks.empty:
        print(call_leaks[['hero_pos', 'street', 'hero_cards', 'gto_action_amount']].head())

    fold_leaks = df[
        (df['hero_action'] == 'FOLD') & 
        (df['gto_action'] != 'FOLD')
    ]
    print(f"\n  Folded when GTO was to play: {len(fold_leaks)} time(s)")
    if not fold_leaks.empty:
        print(fold_leaks[['hero_pos', 'street', 'hero_cards', 'gto_action']].head())

    print("\n[Hero's Average Action Amounts (in chips)]")
    bet_raise_actions = df[df['hero_action'].isin(['BET', 'RAISE'])]
    if not bet_raise_actions.empty:
        bet_raise_actions['hero_action_amount'] = pd.to_numeric(bet_raise_actions['hero_action_amount'], errors='coerce')
        
        print(bet_raise_actions.groupby(['hero_pos', 'street'])['hero_action_amount'].mean().unstack(fill_value=0).applymap(lambda x: f"{x:.2f} chips"))
    else:
        print("  No Bet or Raise actions logged.")


def main():
    parser = argparse.ArgumentParser(description="Analyze PokerNow GTO Session Logs")
    parser.add_argument(
        '--file', 
        type=str, 
        default=None,
        help="Path to a specific log file to analyze. (Default: latest)"
    )
    args = parser.parse_args()

    if args.file:
        if os.path.exists(args.file):
            analyze_session(args.file)
        else:
            print(f"Error: File not found: {args.file}")
            return
    else:
        log_files = glob.glob(os.path.join(LOG_DIR, "*.csv"))
        if not log_files:
            print(f"No log files found in {LOG_DIR}")
            return
            
        latest_log = max(log_files, key=os.path.getctime)
        analyze_session(latest_log)

if __name__ == "__main__":
    main()