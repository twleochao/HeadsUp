import numpy as np
import pandas as pd
from tqdm import tqdm
import random
import eval7
from gto_oracle import GTOOracle
from src.core.feature_eng import create_feature_vector
from src.core.datatypes import Position

NUM_SAMPLES_TO_GENERATE = 50000
DATASET_SAVE_PATH = "data/training_dataset.csv"
POSITIONS = [Position.BTN, Position.SB, Position.BB, Position.UTG, Position.LJ, Position.CO]
BIG_BLIND = 2.0

def generate_random_scenario():
    deck = eval7.Deck()
    
    hero_cards = [str(c) for c in deck.deal(2)]
    
    street = random.choice(["FLOP", "TURN", "RIVER"])
    num_board_cards = {"FLOP": 3, "TURN": 4, "RIVER": 5}[street]
    board_cards = [str(c) for c in deck.deal(num_board_cards)]
    
    hero_pos = random.choice(POSITIONS)
    
    pot_bbs = random.uniform(3.0, 50.0)
    pot_value = pot_bbs * BIG_BLIND
    
    bet_to_call_bbs = 0.0
    if random.random() < 0.5:
        bet_to_call_bbs = random.uniform(0.0, pot_bbs)
    bet_to_call = bet_to_call_bbs * BIG_BLIND
    
    return hero_cards, board_cards, hero_pos, pot_value, bet_to_call

def main():
    print(f"Generating {NUM_SAMPLES_TO_GENERATE} postflop training samples...")
    oracle = GTOOracle()
    
    all_features = []
    all_labels = []

    for _ in tqdm(range(NUM_SAMPLES_TO_GENERATE)):
        hero_cards, board, pos, pot, bet = generate_random_scenario()
        
        y_label = oracle.get_gto_action(hero_cards, board, bet)
        
        X_features = create_feature_vector(
            hero_cards=hero_cards,
            board_cards=board,
            hero_pos=pos,
            pot_value=pot,
            bet_to_call=bet,
            big_blind=BIG_BLIND
        )
        
        all_features.append(X_features)
        all_labels.append(y_label)

    X_df = pd.DataFrame(all_features)
    y_df = pd.DataFrame(all_labels, columns=["action"])
    
    dataset = pd.concat([X_df, y_df], axis=1)
    dataset.to_csv(DATASET_SAVE_PATH, index=False)
    
    print(f"\nSuccessfully generated and saved dataset to {DATASET_SAVE_PATH}")
    print("Action distribution in generated data:")
    print(y_df['action'].value_counts(normalize=True))

if __name__ == "__main__":
    main()