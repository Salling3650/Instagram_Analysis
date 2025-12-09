#!/usr/bin/env python3
"""Instagram Follower Analysis - Find accounts not following you back."""

from bs4 import BeautifulSoup
import csv
import os


def load_ignore_list(file_path='ignore_list.txt'):
    """Load usernames from ignore list file (one username per line)."""
    if not os.path.exists(file_path):
        return set()
    
    ignored = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            username = line.strip()
            if username and not username.startswith('#'):  # Allow comments
                ignored.add(username)
    return ignored


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
    ignored_users = load_ignore_list('ignore_list.txt')
    
    not_following_back = following - followers
    not_following_back_filtered = not_following_back - ignored_users

    total_following = len(following)
    total_followers = len(followers)
    mutual_following = len(following & followers)
    not_following_back_count = len(not_following_back)
    ignored_count = len(not_following_back & ignored_users)
    filtered_count = len(not_following_back_filtered)

    # Display results
    print("Instagram follower analysis") 
    print(f"\nYou follow: {total_following} accounts")
    print(f"Follow you: {total_followers} accounts")
    print(f"Mutual following: {mutual_following} accounts")
    print(f"Don't follow you back: {not_following_back_count} accounts")
    if ignored_count > 0:
        print(f"  - Ignored: {ignored_count} accounts")
        print(f"  - Remaining: {filtered_count} accounts")
    print()

    for username in sorted(not_following_back_filtered):
        print(f"  • {username}")

    # Save results as CSV (keeps terminal output intact)
    with open('not_following_back.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['username'])
        for username in sorted(not_following_back_filtered):
            writer.writerow([username,])

    print(f"\nResults saved to: not_following_back.csv")
