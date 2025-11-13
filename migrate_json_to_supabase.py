#!/usr/bin/env python3
"""Migrate JSON state to Supabase database."""
import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')


def migrate():
    """Migrate videos from JSON to Supabase."""
    # Load JSON state
    state_path = 'state/dailymotion_videos.json'

    print(f'Loading {state_path}...')
    with open(state_path, 'r', encoding='utf-8') as f:
        state = json.load(f)

    print(f'Found {len(state)} videos in JSON')

    # Connect to Supabase
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Prepare data for insertion
    videos_to_insert = []

    for key, video in state.items():
        # Map JSON fields to database columns
        db_video = {
            'platform': video.get('platform', 'dailymotion'),
            'video_id': video.get('video_id'),
            'url': video.get('url'),
            'title': video.get('title'),
            'uploader': video.get('uploader'),
            'duration_sec': video.get('duration_sec'),
            'publish_time': video.get('publish_time'),
            'views': video.get('views'),
            'raw_score': video.get('raw_score'),
            'score': video.get('score'),
            'series_id': video.get('series_id'),
            'source_term': video.get('source_term'),
            'geoblocking': video.get('geoblocking'),  # List/array
            'blocked_regions': video.get('blocked_regions'),  # List/array
            'api_status': video.get('api_status'),
            'api_last_checked': video.get('api_last_checked'),
            'first_seen': video.get('first_seen'),
        }

        # Skip if missing required fields
        if not db_video['video_id'] or not db_video['first_seen']:
            print(f'  Skipping {key}: missing video_id or first_seen')
            continue

        videos_to_insert.append(db_video)

    print(f'\nPrepared {len(videos_to_insert)} videos for insertion')

    # Insert in batches (Supabase limit: ~1000 per request)
    batch_size = 500
    total_inserted = 0
    errors = []

    for i in range(0, len(videos_to_insert), batch_size):
        batch = videos_to_insert[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(videos_to_insert) + batch_size - 1) // batch_size

        print(f'Inserting batch {batch_num}/{total_batches} ({len(batch)} videos)...')

        try:
            response = supabase.table('videos').upsert(batch).execute()
            total_inserted += len(batch)
            print(f'  ✓ Inserted {len(batch)} videos')
        except Exception as e:
            print(f'  ✗ Error inserting batch: {e}')
            errors.append((batch_num, str(e)))

    print(f'\n{"="*50}')
    print(f'Migration completed!')
    print(f'  Total inserted: {total_inserted}/{len(videos_to_insert)}')

    if errors:
        print(f'  Errors: {len(errors)}')
        for batch_num, err in errors[:5]:
            print(f'    Batch {batch_num}: {err}')

    # Verify
    print(f'\nVerifying...')
    count_response = supabase.table('videos').select('count', count='exact').execute()
    print(f'Videos in database: {count_response.count}')

    return True


if __name__ == '__main__':
    migrate()
