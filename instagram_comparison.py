#!/usr/bin/env python3
"""Instagram Follower Analysis - Find accounts not following you back."""

from bs4 import BeautifulSoup
import csv


def extract_usernames_from_html(file_path):
    """Extract Instagram usernames from HTML export file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    usernames = set()
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        if '_u/' in href:
            username = href.split('_u/')[-1]
            if username:
                usernames.add(username)
        elif 'instagram.com/' in href:
            username = link.get_text().strip()
            if username and not username.startswith('http'):
                usernames.add(username)
    
    for h2 in soup.find_all('h2'):
        username = h2.get_text().strip()
        if username and not username.startswith('http'):
            usernames.add(username)
    
    return usernames


if __name__ == '__main__':
    # Load and analyze
    following = extract_usernames_from_html('data/following.html')
    followers = extract_usernames_from_html('data/followers_1.html')
    not_following_back = following - followers

    total_following = len(following)
    total_followers = len(followers)
    mutual_following = len(following & followers)
    not_following_back_count = len(not_following_back)

    # Display results
    print("\n" + "="*50)
    print("INSTAGRAM FOLLOWER ANALYSIS")
    print("="*50)
    print(f"\nYou follow: {total_following} accounts")
    print(f"Follow you: {total_followers} accounts")
    print(f"Mutual following: {mutual_following} accounts")
    print(f"Don't follow you back: {not_following_back_count} accounts\n")

    for username in sorted(not_following_back):
        print(f"  • {username}")

    # Save results as CSV (keeps terminal output intact)
    with open('not_following_back.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['username', 'follows_back'])
        for username in sorted(not_following_back):
            writer.writerow([username, 'no'])

    print(f"\n{'='*50}\nResults saved to: not_following_back.csv")
