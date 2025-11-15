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


def get_existing_video_ids(video_ids: List[str], platform: str = 'dailymotion', batch_size: int = 1000) -> set:
    """Batch check which video IDs exist. Returns set of existing IDs."""
    if not video_ids:
        return set()

    client = get_client()
    existing = set()

    # Process in batches to avoid URL length limits
    for i in range(0, len(video_ids), batch_size):
        batch = video_ids[i:i + batch_size]
        response = client.table('videos').select('video_id').eq('platform', platform).in_('video_id', batch).execute()
        existing.update(row['video_id'] for row in response.data)

    return existing


def insert_videos(videos: List[Dict]) -> int:
    """Insert/update videos (upsert). Returns count."""
    if not videos:
        return 0
    client = get_client()
    client.table('videos').upsert(videos).execute()
    return len(videos)


def get_videos_to_recheck(min_days: int = 2, max_days: int = 30) -> List[Dict]:
    """
    Get videos needing recheck (min_days to max_days old, active status).
    Set min_days=0 to include all videos up to max_days old.
    """
    client = get_client()
    today = date.today()

    query = client.table('videos').select('*')

    # Apply date filters
    if max_days > 0:
        min_date = date.fromordinal(today.toordinal() - max_days)
        query = query.gte('first_seen', min_date.isoformat())

    if min_days > 0:
        max_date = date.fromordinal(today.toordinal() - min_days)
        query = query.lte('first_seen', max_date.isoformat())

    response = query.execute()

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
