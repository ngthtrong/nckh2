"""
Download flood-related images from Wikimedia Commons using Category API.
Saves images to dataset/image_data/raw/wikimedia_flood/{category_tag}/
Uses direct image URLs + aggressive rate-limit handling.
"""
import urllib.request
import urllib.parse
import json
import os
import time
import random

DEST = 'dataset/image_data/raw/wikimedia_flood'
API = 'https://commons.wikimedia.org/w/api.php'
HEADERS = {'User-Agent': 'FloodAI-Research/1.0 (academic non-commercial; contact noreply@example.com)'}
MAX_PER_CAT = 60
IMG_EXTS = ('.jpg', '.jpeg', '.png')
DELAY = 3.0          # seconds between requests (Wikimedia rate limit is strict)
RETRY_DELAY = 30.0   # seconds to wait after 429

# Wikimedia Commons categories directly relevant to flood/rescue imagery
CATEGORIES = [
    ('flood_vietnam',       'Floods in Vietnam'),
    ('flood_2020_vn',       '2020_floods_in_Vietnam'),
    ('flood_2021_vn',       '2021_floods_in_Vietnam'),
    ('flood_harvey',        'Effects of Hurricane Harvey in Texas'),
    ('flood_katrina',       'Flooding caused by Hurricane Katrina'),
    ('flood_general',       'Flood rescue'),
    ('flood_asia',          'Flooding in Asia'),
    ('flood_streets',       'Floods in streets'),
    ('flood_houses',        'Flooded houses'),
    ('natural_disaster_img','Natural disaster images'),
]


def get_category_images(category, limit=MAX_PER_CAT):
    """Fetch image titles from a Wikimedia Commons category."""
    titles = []
    cmcontinue = ''
    while len(titles) < limit:
        url = (f'{API}?action=query&list=categorymembers'
               f'&cmtitle=Category:{urllib.parse.quote(category)}'
               f'&cmtype=file&cmlimit=50&format=json'
               + (f'&cmcontinue={urllib.parse.quote(cmcontinue)}' if cmcontinue else ''))
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            data = json.loads(urllib.request.urlopen(req, timeout=20).read())
            members = data.get('query', {}).get('categorymembers', [])
            for m in members:
                t = m['title']
                if any(t.lower().endswith(ext) for ext in IMG_EXTS):
                    titles.append(t)
            if 'continue' not in data:
                break
            cmcontinue = data['continue'].get('cmcontinue', '')
            if not cmcontinue:
                break
            time.sleep(DELAY)
        except Exception as e:
            print(f'  Category query error: {e}')
            break
    return titles[:limit]


def batch_imageinfo(titles):
    """Get direct image URLs for a batch of titles (up to 50 at once)."""
    result = {}
    for i in range(0, len(titles), 20):
        batch = titles[i:i+20]
        encoded = '|'.join(urllib.parse.quote(t) for t in batch)
        url = (f'{API}?action=query&titles={encoded}'
               f'&prop=imageinfo&iiprop=url|mime|size&format=json')
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            data = json.loads(urllib.request.urlopen(req, timeout=20).read())
            for _, page in data['query']['pages'].items():
                if 'imageinfo' in page:
                    info = page['imageinfo'][0]
                    mime = info.get('mime', '')
                    size = info.get('size', 0)
                    if mime.startswith('image/') and size < 15_000_000:  # skip huge files
                        result[page['title']] = info['url']
            time.sleep(DELAY)
        except Exception as e:
            print(f'  Imageinfo error: {e}')
    return result


def download_file(url, fpath, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=45) as r, open(fpath, 'wb') as f:
                f.write(r.read())
            return True
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = RETRY_DELAY * (attempt + 1) + random.uniform(0, 2)
                print(f'  429 rate-limited, waiting {wait:.1f}s ...')
                time.sleep(wait)
            else:
                return False
        except Exception:
            return False
    return False


def download_category(tag, category):
    dest = os.path.join(DEST, tag)
    os.makedirs(dest, exist_ok=True)
    print(f'\n[{tag}] Category: "{category}"')
    titles = get_category_images(category)
    print(f'  Found {len(titles)} image files')
    if not titles:
        return 0

    url_map = batch_imageinfo(titles)
    print(f'  Got direct URLs for {len(url_map)} images')

    downloaded = 0
    for title, img_url in url_map.items():
        fname = title.replace('File:', '').replace('/', '_').replace(' ', '_')
        fpath = os.path.join(dest, fname)
        if os.path.exists(fpath):
            downloaded += 1
            continue
        if download_file(img_url, fpath):
            downloaded += 1
            if downloaded % 10 == 0:
                print(f'  Progress: {downloaded}/{len(url_map)}')
            time.sleep(DELAY + random.uniform(0, 0.5))
        else:
            print(f'  Failed: {title}')
    print(f'  Saved {downloaded} images to {dest}')
    return downloaded


if __name__ == '__main__':
    os.makedirs(DEST, exist_ok=True)
    total = 0
    for tag, cat in CATEGORIES:
        total += download_category(tag, cat)
    print(f'\nTotal downloaded: {total} images')

