#!/usr/bin/env python3
"""Instagram Follower Analysis - Find accounts not following you back."""

import csv
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup


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


def cleanup_ignore_list(following, file_path='ignore_list.txt'):
    """Remove usernames from ignore list that you no longer follow.
    
    Args:
        following: Set of usernames you're currently following
        file_path: Path to the ignore list file
    
    Returns:
        Set of usernames that were removed from the ignore list
    """
    if not os.path.exists(file_path):
        return set()
    
    # Read all lines from the file (including comments)
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    removed_users = set()
    updated_lines = []
    
    for line in lines:
        username = line.strip()
        
        # Keep comments and empty lines as-is
        if not username or username.startswith('#'):
            updated_lines.append(line)
        else:
            # Only keep username if you're still following them
            if username in following:
                updated_lines.append(line)
            else:
                removed_users.add(username)
    
    # Write back the updated list if changes were made
    if removed_users:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
    
    return removed_users


def extract_usernames_from_json(file_path):
    """Extract Instagram usernames from JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    usernames = set()
    
    # Handle Instagram's JSON export format
    if isinstance(data, dict):
        # Check for relationships_following or relationships_followers keys
        if 'relationships_following' in data:
            for item in data['relationships_following']:
                if 'title' in item:
                    usernames.add(item['title'])
                elif 'string_list_data' in item:
                    for entry in item['string_list_data']:
                        if 'value' in entry:
                            usernames.add(entry['value'])
        elif 'relationships_followers' in data:
            for item in data['relationships_followers']:
                if 'title' in item:
                    usernames.add(item['title'])
                elif 'string_list_data' in item:
                    for entry in item['string_list_data']:
                        if 'value' in entry:
                            usernames.add(entry['value'])
        # Handle simple dict with usernames or data key
        elif 'usernames' in data:
            if isinstance(data['usernames'], list):
                usernames = set(data['usernames'])
        elif 'data' in data:
            if isinstance(data['data'], list):
                usernames = set(data['data'])
    elif isinstance(data, list):
        # Handle array format (like followers_1.json)
        for item in data:
            if isinstance(item, str):
                # Simple list of usernames
                usernames.add(item)
            elif isinstance(item, dict):
                # Check for title field
                if 'title' in item and item['title']:
                    usernames.add(item['title'])
                # Check for string_list_data with value field
                if 'string_list_data' in item:
                    for entry in item['string_list_data']:
                        if isinstance(entry, dict) and 'value' in entry:
                            usernames.add(entry['value'])
    
    return usernames


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


def extract_usernames(file_path):
    """Extract usernames from either HTML or JSON file based on extension."""
    if file_path.endswith('.json'):
        return extract_usernames_from_json(file_path)
    else:
        return extract_usernames_from_html(file_path)


def parse_likes_data(file_path):
    """Parse likes data from post.json or storie.json files.
    
    Expected format:
    {
        "Time(290124)": ["username1", "username2", "username3"],
        "Time(300124)": ["username1", "username3"]
    }
    """
    if not os.path.exists(file_path):
        return {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Flatten structure to get username -> list of timestamps
    likes_by_user = {}
    for time_key, usernames in data.items():
        for username in usernames:
            if username not in likes_by_user:
                likes_by_user[username] = []
            likes_by_user[username].append(time_key)
    
    return likes_by_user


def get_follower_since_timestamp(username, followers_data):
    """Get the timestamp when a user started following (from followers_1.json)."""
    try:
        with open(followers_data, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            if 'string_list_data' in item:
                for entry in item['string_list_data']:
                    if entry.get('value') == username:
                        return entry.get('timestamp', 0)
    except:
        pass
    return 0


def generate_connection_json(followers, following, posts_likes, stories_likes, followers_data_path='data/followers_1.json'):
    """Generate connection.json with engagement metrics for each follower.
    
    Metrics:
    - Followed by since: timestamp when they started following
    - Liked total: total likes on posts + stories
    - Liked per post/story: average likes per content piece
    - Liked per time since followed by: likes per day since following
    - Total score: combined engagement score
    """
    connections = []
    current_time = int(datetime.now().timestamp())
    
    for username in followers:
        # Get follower timestamp
        followed_since = get_follower_since_timestamp(username, followers_data_path)
        followed_since_date = datetime.fromtimestamp(followed_since).strftime('%Y-%m-%d %H:%M:%S') if followed_since > 0 else 'Unknown'
        
        # Count likes
        post_likes_count = len(posts_likes.get(username, []))
        story_likes_count = len(stories_likes.get(username, []))
        total_likes = post_likes_count + story_likes_count
        
        # Calculate metrics
        total_content = post_likes_count + story_likes_count
        likes_per_content = total_likes / total_content if total_content > 0 else 0
        
        # Calculate days since followed
        days_since_followed = (current_time - followed_since) / 86400 if followed_since > 0 else 1
        days_since_followed = max(days_since_followed, 1)  # Avoid division by zero
        
        likes_per_day = total_likes / days_since_followed
        
        # Calculate total score (weighted combination)
        # Weight: total likes (40%) + likes per content (30%) + likes per day (30%)
        total_score = (total_likes * 0.4) + (likes_per_content * 30 * 0.3) + (likes_per_day * 10 * 0.3)
        
        connection_data = {
            'username': username,
            'followed_by_since': followed_since_date,
            'followed_by_timestamp': followed_since,
            'total_likes': total_likes,
            'post_likes': post_likes_count,
            'story_likes': story_likes_count,
            'likes_per_content': round(likes_per_content, 2),
            'likes_per_day': round(likes_per_day, 4),
            'days_since_followed': round(days_since_followed, 1),
            'total_score': round(total_score, 2),
            'is_following_back': username in following
        }
        
        connections.append(connection_data)
    
    # Sort by total score (descending)
    connections.sort(key=lambda x: x['total_score'], reverse=True)
    
    return connections


if __name__ == '__main__':
    # Load and analyze
    following = extract_usernames('data/following.json')
    followers = extract_usernames('data/followers_1.json')
    
    # Clean up ignore list (remove users you no longer follow)
    removed_from_ignore_list = cleanup_ignore_list(following, 'ignore_list.txt')
    if removed_from_ignore_list:
        print("🧹 Cleaned up ignore list:")
        print(f"   Removed {len(removed_from_ignore_list)} user(s) you no longer follow:")
        for username in sorted(removed_from_ignore_list):
            print(f"   • {username}")
        print()
    
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
    
    # Parse likes data from posts and stories if available
    #print("\n" + "="*50)
    #print("Generating connection analysis...")
    #print("="*50)
    
    #posts_likes = parse_likes_data('post.json')
    #stories_likes = parse_likes_data('storie.json')
    
    # Generate connection data with engagement metrics
    #connections = generate_connection_json(
    #    followers, 
    #    following, 
    #    posts_likes, 
    #    stories_likes,
    #    'data/followers_1.json'
    #)
    
    # Save connection.csv
    #with open('connection.csv', 'w', newline='', encoding='utf-8') as f:
    #    if len(connections) > 0:
    #        writer = csv.DictWriter(f, fieldnames=[
    #            'username', 'followed_by_since', 'followed_by_timestamp', 
    #            'total_likes', 'post_likes', 'story_likes', 
    #            'likes_per_content', 'likes_per_day', 'days_since_followed',
    #            'total_score', 'is_following_back'
    #        ])
    #        writer.writeheader()
    #        writer.writerows(connections)
    
    #print(f"\nConnection analysis complete!")
    #print(f"Total connections analyzed: {len(connections)}")
    
    #if len(connections) > 0:
    #    print(f"\nTop 10 engaged followers (by total score):")
    #    for i, conn in enumerate(connections[:10], 1):
    #        print(f"  {i}. {conn['username']}")
    #        print(f"     Score: {conn['total_score']:.2f} | Likes: {conn['total_likes']} " +
    #              f"(Posts: {conn['post_likes']}, Stories: {conn['story_likes']}) | " +
    #              f"Since: {conn['followed_by_since']}")
    
    #print(f"\nDetailed results saved to: connection.csv")