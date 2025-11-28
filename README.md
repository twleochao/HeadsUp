# HeadsUp

A real-time GTO poker assistant and HUD for No Limit Texas Hold'em. Designed for live decision support during live play.

## Features

* **Real-Time Overlay:** Transparent PySide6 HUD that overlays directly on the game window.
* **<20ms Latency:** Optimized multi-threaded architecture for instant decision support.
* **GTO-Lite Engine:** XGBoost model trained on 50,000+ solver-generated hands (95.6% accuracy).
* **Live Perception:** Selenium-based API integration for accurate game state polling.
* **Action Logging:** Automatically logs "Hero" decisions vs. GTO advice for post-session analysis.

## Installation

Clone the repository:

```bash
git clone https://github.com/twleochao/pdfim.git
cd pdfim
pip install -r requirements.txt
```

## Usage

1. Launch your poker client.
2. Run the HUD:

```bash
python main.py
```
The overlay will automatically detect the game window and attach itself. 


## Dependencies

* Python 3.8+
* PySide6 (Qt for Python)
* Selenium
* XGBoost
* Pandas & Scikit-learn
* eval7

## License

MIT License
