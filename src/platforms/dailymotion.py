from __future__ import annotations
import os
import time
from typing import Dict, Iterable, List, Optional

import json
import urllib.parse
import urllib.request


DAILYMOTION_API = "https://api.dailymotion.com/videos"


def _http_get(url: str, timeout: int = 15) -> Dict:
    req = urllib.request.Request(url, headers={
        'User-Agent': 'col-piracy/0.1 (+internal)'
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))


def parse_geoblocking(geoblocking: List) -> tuple:
    """
    Parse Dailymotion's geoblocking field into blocked and available regions.

    Args:
        geoblocking: Array from API, e.g. ["deny", "CN", "US"] or ["allow", "FR", "JP"]

    Returns:
        Tuple of (blocked_regions, available_regions)

    Examples:
        ["deny", "CN", "US"] → (["CN", "US"], [])  # blocked in CN and US
        ["allow", "US", "JP"] → ([], ["US", "JP"])  # only available in US and JP
        [] or ["allow"] → ([], [])  # available globally
    """
    if not geoblocking or geoblocking == ["allow"]:
        # Empty or just "allow" = globally available
        return ([], [])

    mode = geoblocking[0] if geoblocking else "allow"
    regions = geoblocking[1:] if len(geoblocking) > 1 else []

    if mode == "deny":
        return (regions, [])  # These regions are blocked
    else:  # mode == "allow"
        return ([], regions)  # Only available in these regions


def check_video_geo_availability(video_id: str, regions: List[str], sleep_sec: float = 0.3) -> Dict[str, Optional[bool]]:
    """
    DEPRECATED: Use get_video_status() with geoblocking field instead.
    This function makes multiple API calls which is inefficient.

    Check if a video is available in each specified region using ams_country parameter.

    Args:
        video_id: Dailymotion video ID (e.g., 'x123abc')
        regions: List of country codes (e.g., ['US', 'CN', 'JP'])
        sleep_sec: Delay between API calls

    Returns:
        Dict mapping region to availability:
        - True: video is available in that region
        - False: video is blocked in that region (403/451 error)
        - None: unknown (other error)
    """
    availability = {}

    for region in regions:
        q = urllib.parse.urlencode({
            'fields': 'id',
            'ams_country': region,
        })
        url = f"https://api.dailymotion.com/video/{video_id}?{q}"

        try:
            _http_get(url)
            availability[region] = True
        except urllib.error.HTTPError as e:
            if e.code in (403, 451):
                # 403 Forbidden or 451 Unavailable For Legal Reasons = geo-blocked
                availability[region] = False
            elif e.code == 404:
                # Video doesn't exist
                availability[region] = None
            else:
                # Other error, mark as unknown
                print(f"  Warning: Unexpected HTTP {e.code} for video {video_id} in region {region}")
                availability[region] = None
        except Exception as e:
            print(f"  Warning: Geo-check failed for video {video_id} in region {region}: {e}")
            availability[region] = None

        time.sleep(sleep_sec)

    return availability


def get_video_status(video_id: str) -> Dict:
    """
    Check the status of a specific video by ID (includes geo-blocking info).

    Args:
        video_id: Dailymotion video ID (e.g., 'x123abc')

    Returns:
        Dict with status information:
        - exists: bool (False if 404)
        - private: bool
        - password_protected: bool
        - status: str (e.g., 'ready', 'rejected', 'processing')
        - published: bool
        - geoblocking: list (e.g., ["deny", "CN"] or ["allow", "US", "JP"])
        - views_total: int
        - updated_time: str
        - duration: int
    """
    fields = [
        'id', 'private', 'password_protected', 'status', 'published',
        'geoblocking', 'views_total', 'updated_time', 'duration'
    ]
    q = urllib.parse.urlencode({'fields': ','.join(fields)})
    url = f"https://api.dailymotion.com/video/{video_id}?{q}"

    try:
        data = _http_get(url)
        return {
            'exists': True,
            'private': data.get('private', False),
            'password_protected': data.get('password_protected', False),
            'status': data.get('status', ''),
            'published': data.get('published', False),
            'geoblocking': data.get('geoblocking', []),
            'views_total': data.get('views_total', 0),
            'updated_time': data.get('updated_time', ''),
            'duration': data.get('duration', 0),
        }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {'exists': False}
        # Fail fast - don't catch other errors
        raise
    except Exception:
        # Fail fast - let the error propagate
        raise


def search_videos(terms: Iterable[str], per_term_limit: int = 10, sleep_sec: float = 0.5) -> List[Dict]:
    """
    Search for videos on Dailymotion.

    Args:
        terms: Search terms to query
        per_term_limit: Total number of results to fetch per term (will use pagination if > 100)
        sleep_sec: Sleep time between API calls

    Returns:
        List of video dictionaries

    Note:
        Dailymotion API limit is 100 per page. If per_term_limit > 100,
        will automatically fetch multiple pages.
    """
    fields = [
        'id', 'title', 'url', 'owner.username', 'owner.id', 'duration', 'created_time', 'views_total'
    ]
    results: List[Dict] = []

    for term in terms:
        # Calculate how many pages we need (max 100 per page)
        page_size = min(per_term_limit, 100)
        total_needed = per_term_limit
        total_fetched = 0
        page = 1

        while total_fetched < total_needed:
            # Build query for this page
            q = urllib.parse.urlencode({
                'search': term,
                'fields': ','.join(fields),
                'limit': page_size,
                'page': page,
                'sort': 'relevance',
            })
            url = f"{DAILYMOTION_API}?{q}"

            try:
                data = _http_get(url)
            except Exception as e:
                # Surface but continue
                print(f"Dailymotion query failed for term='{term}' page={page}: {e}")
                break

            items = data.get('list', []) or []
            if not items:
                # No more results
                break

            for item in items:
                item['__source_term'] = term
                results.append(item)
                total_fetched += 1

                if total_fetched >= total_needed:
                    break

            # Check if there are more pages
            has_more = data.get('has_more', False)
            if not has_more or total_fetched >= total_needed:
                break

            page += 1
            time.sleep(sleep_sec)

        # Sleep between terms (already slept between pages)
        if total_fetched > 0:
            time.sleep(sleep_sec)

    return results

