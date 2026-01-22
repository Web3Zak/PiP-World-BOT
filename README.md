# PiP-World-BOT

Automates daily tasks on **mm.pip.world** using **Playwright** and **ADS Browser**.

## Features
- Start and stop ADS browser profiles by ID
- Automated Daily Check-In
- Share and claim XP flow
- Collects statistics: current streak, XP rank, badges
- Graceful shutdown of browser and ADS profiles

## Configuration
config.json must be a list of accounts.

```json
[
  {
    "id": "YOUR_ADS_PROFILE_ID",
    "name": "Account_1"
  },
  {
    "id": "YOUR_ADS_PROFILE_ID_2",
    "name": "Account_2"
  }
]
```
Fields:
- id (required): ADS profile ID
- name (optional): Profile name used in logs

## Installation
Requirements:
- Python 3.10 or higher
- ADS Browser with local API enabled
- Playwright

Install dependencies:
```
pip install playwright httpx
playwright install chromium
```
## Usage
```
python main.py
```
Accounts are processed sequentially.  
An error in one profile does not stop the others.
