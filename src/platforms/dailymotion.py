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


def search_videos(terms: Iterable[str], per_term_limit: int = 10, sleep_sec: float = 0.5) -> List[Dict]:
    fields = [
        'id', 'title', 'url', 'owner.username', 'owner.id', 'duration', 'created_time', 'views_total'
    ]
    results: List[Dict] = []
    for term in terms:
        q = urllib.parse.urlencode({
            'search': term,
            'fields': ','.join(fields),
            'limit': per_term_limit,
            'sort': 'relevance',
        })
        url = f"{DAILYMOTION_API}?{q}"
        try:
            data = _http_get(url)
        except Exception as e:
            # Surface but continue
            print(f"Dailymotion query failed for term='{term}': {e}")
            continue
        for item in data.get('list', []) or []:
            item['__source_term'] = term
            results.append(item)
        time.sleep(sleep_sec)
    return results

