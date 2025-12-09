# Instagram Analysis

This project analyzes Instagram data to find accounts you follow that don't follow you back.

## Files
- `instagram_comparison.py`: Python script to analyze followers and following
- `data/`: Place your Instagram data export files here (`followers_1.html` and `following.html`)
- `not_following_back.csv`: Output file with accounts not following you back

## Setup
1. Download your Instagram data:
   - Go to Instagram Settings → Your activity → Download your information
   - Request a download of your data
   - Extract the files to the `data/` folder
2. Install required dependencies:
   ```bash
   pip install beautifulsoup4
   ```

## Usage
Run the analysis script:
```bash
python instagram_comparison.py
```

The script will:
- Analyze your followers and following lists
- Display a summary of mutual follows and non-followers
- Save the results to `not_following_back.csv`

Ignorelist:
- Alternativly you can add usernames to `ignore_list.txt`

## Note
Data files in `data/` and `not_following_back.csv` are ignored by Git for privacy.