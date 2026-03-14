import os
import json
import re
import argparse
import sys

try:
    from googleapiclient.discovery import build
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import SRTFormatter
except ImportError:
    print("Missing dependencies. Please install them:")
    print("pip install google-api-python-client youtube-transcript-api")
    sys.exit(1)

def load_config(config_path):
    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}")
        sys.exit(1)
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_channel_videos(api_key, channel_id):
    """
    Fetches all video IDs and titles from a YouTube channel using the Data API.
    """
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    # 1. Get the uploads playlist ID
    try:
        res = youtube.channels().list(id=channel_id, part='contentDetails').execute()
        if not res['items']:
            print(f"Channel ID {channel_id} not found.")
            sys.exit(1)
        uploads_playlist_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    except Exception as e:
        print(f"Error fetching channel details: {e}")
        sys.exit(1)

    videos = []
    next_page_token = None
    
    print(f"Fetching video list for channel {channel_id}...")

    while True:
        pl_request = youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
            part='snippet',
            maxResults=50,
            pageToken=next_page_token
        )
        pl_response = pl_request.execute()
        
        for item in pl_response['items']:
            title = item['snippet']['title']
            video_id = item['snippet']['resourceId']['videoId']
            videos.append({'title': title, 'id': video_id})
            
        next_page_token = pl_response.get('nextPageToken')
        if not next_page_token:
            break
            
    return videos

def sanitize_filename(name):
    # Remove characters invalid for filesystems
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def download_subtitles(videos, output_base):
    if not os.path.exists(output_base):
        os.makedirs(output_base)
        
    formatter = SRTFormatter()
    
    for video in videos:
        title = video['title']
        video_id = video['id']
        safe_title = sanitize_filename(title)
        
        # Structure: rawsubs/<video name>/<video_name>.srt
        video_dir = os.path.join(output_base, safe_title)
        if not os.path.exists(video_dir):
            os.makedirs(video_dir)
            
        output_path = os.path.join(video_dir, f"{safe_title}.srt")
        
        if os.path.exists(output_path):
            # Skip if already exists
            continue
            
        print(f"Processing: {title}")
        
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Prioritize auto-generated English
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
            except:
                 # Fallback to manual if auto is missing (optional, but robust)
                transcript = transcript_list.find_manually_created_transcript(['en'])
            
            srt_data = formatter.format_transcript(transcript.fetch())
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_data)
            print(f"  Saved to {output_path}")
                
        except Exception:
            print(f"  No English subtitles found for {title}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download auto-generated subtitles from a YouTube channel.")
    parser.add_argument("--config", default="youtube_config.json", help="Path to the youtube config file")
    parser.add_argument("--output", default="rawsubs", help="Output directory base")
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    api_key = config.get("api_key")
    channel_id = config.get("channel_id")
    
    if not api_key or not channel_id:
        print("Config must contain 'api_key' and 'channel_id'")
        sys.exit(1)
        
    videos = get_channel_videos(api_key, channel_id)
    print(f"Found {len(videos)} videos.")
    
    download_subtitles(videos, args.output)