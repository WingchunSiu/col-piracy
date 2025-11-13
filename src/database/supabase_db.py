"""Supabase database operations for piracy detection system."""
import os
from datetime import date
from typing import List, Dict
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Singleton client
_client: Client = None


def get_client() -> Client:
    """Get Supabase client."""
    global _client
    if _client is None:
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY')
        if not url or not key:
            raise ValueError('SUPABASE_URL and SUPABASE_KEY required')
        _client = create_client(url, key)
    return _client


def video_exists(video_id: str, platform: str = 'dailymotion') -> bool:
    """Check if video exists."""
    client = get_client()
    response = client.table('videos').select('video_id').eq('platform', platform).eq('video_id', video_id).execute()
    return len(response.data) > 0


def insert_videos(videos: List[Dict]) -> int:
    """Insert/update videos (upsert). Returns count."""
    if not videos:
        return 0
    client = get_client()
    client.table('videos').upsert(videos).execute()
    return len(videos)


def get_videos_to_recheck(min_days: int = 2, max_days: int = 30) -> List[Dict]:
    """Get videos needing recheck (min_days to max_days old, active status)."""
    client = get_client()
    today = date.today()

    min_date = date.fromordinal(today.toordinal() - max_days)
    max_date = date.fromordinal(today.toordinal() - min_days)

    response = client.table('videos') \
        .select('*') \
        .gte('first_seen', min_date.isoformat()) \
        .lte('first_seen', max_date.isoformat()) \
        .execute()

    # Filter for active or null status (Supabase doesn't support .in_([..., None]))
    return [v for v in response.data if v.get('api_status') in ('active', None)]


def update_video_status(video_id: str, api_status: str, platform: str = 'dailymotion'):
    """Update video status after recheck."""
    client = get_client()
    client.table('videos').update({
        'api_status': api_status,
        'api_last_checked': date.today().isoformat()
    }).eq('platform', platform).eq('video_id', video_id).execute()


def delete_removed_videos() -> int:
    """Delete removed videos. Returns count deleted."""
    client = get_client()
    response = client.table('videos').delete().eq('api_status', 'removed').execute()
    return len(response.data) if response.data else 0


def get_all_videos_for_report(max_days: int = 30) -> List[Dict]:
    """Get all videos for status report (within max_days)."""
    client = get_client()
    today = date.today()
    min_date = date.fromordinal(today.toordinal() - max_days)

    response = client.table('videos') \
        .select('*') \
        .gte('first_seen', min_date.isoformat()) \
        .order('first_seen', desc=True) \
        .execute()

    return response.data


def count_videos() -> int:
    """Total video count."""
    client = get_client()
    response = client.table('videos').select('count', count='exact').execute()
    return response.count
