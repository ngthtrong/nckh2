"""
Download flood/disaster images from FEMA Media Library (Public Domain).
FEMA images on media.fema.gov are US Government work = Public Domain.
"""
import urllib.request
import urllib.parse
import json
import os
import time

DEST = 'dataset/image_data/raw/fema_flood'
HEADERS = {'User-Agent': 'Mozilla/5.0 (FloodAI-Research academic)'}
API = 'https://www.fema.gov/api/open/v1/DisasterDeclarationsSummaries'

# FEMA media search API for flood disaster photos
FEMA_MEDIA_API = 'https://www.fema.gov/api/open/v1/FemaWebDisasterSummaries'

# Direct known Public Domain flood images from FEMA + USACE (Wikimedia)
DIRECT_URLS = [
    # FEMA flood/hurricane rescue photos (Public Domain - US Government)
    # Hurricane Katrina
    ('katrina', 'https://upload.wikimedia.org/wikipedia/commons/a/a7/FEMA_-_15620_-_Photograph_by_Jocelyn_Augustino_taken_on_08-30-2005_in_Louisiana.jpg'),
    ('katrina', 'https://upload.wikimedia.org/wikipedia/commons/6/62/FEMA_-_15626_-_Photograph_by_Jocelyn_Augustino_taken_on_08-30-2005_in_Louisiana.jpg'),
    ('katrina', 'https://upload.wikimedia.org/wikipedia/commons/9/9d/FEMA_-_15628_-_Photograph_by_Jocelyn_Augustino_taken_on_08-30-2005_in_Louisiana.jpg'),
    ('katrina', 'https://upload.wikimedia.org/wikipedia/commons/2/25/FEMA_-_15622_-_Photograph_by_Jocelyn_Augustino_taken_on_08-30-2005_in_Louisiana.jpg'),
    # Iowa floods FEMA
    ('iowa', 'https://upload.wikimedia.org/wikipedia/commons/b/b6/Flooding_in_Iowa_City%2C_Iowa_June_2008.jpg'),
    # General flood street rescue
    ('rescue_boat', 'https://upload.wikimedia.org/wikipedia/commons/3/3a/FEMA_-_31645_-_Man_calls_family_during_rising_flood_waters_in_Oklahoma.jpg'),
    # Vietnam specific
    ('vietnam', 'https://upload.wikimedia.org/wikipedia/commons/3/34/A_flood_in_a_town_in_Vietnam.jpg'),
    ('vietnam', 'https://upload.wikimedia.org/wikipedia/commons/d/d2/Flood_Vietnam.jpg'),
    ('vietnam', 'https://upload.wikimedia.org/wikipedia/commons/b/b9/Blue_IFA_W50_truck_crossing_a_river_during_a_flood_in_Vietnam.jpg'),
    # Asian flooding
    ('asia_flood', 'https://upload.wikimedia.org/wikipedia/commons/e/e4/1941_flood_in_Rajshahi.jpg'),
    ('asia_flood', 'https://upload.wikimedia.org/wikipedia/commons/7/74/Flood_2007_Bangladesh.jpg'),
    ('asia_flood', 'https://upload.wikimedia.org/wikipedia/commons/d/dc/2007_Thailand_flood.jpg'),
    ('asia_flood', 'https://upload.wikimedia.org/wikipedia/commons/d/d0/20110810_Thailand_flooding.jpg'),
    # Philippines flooding
    ('philippines', 'https://upload.wikimedia.org/wikipedia/commons/f/f8/Flooding_in_Dagupan_2009.jpg'),
    # Indonesia flooding
    ('indonesia', 'https://upload.wikimedia.org/wikipedia/commons/6/64/Jakarta_flood_2007.jpg'),
    # No-flood normal street
    ('no_flood', 'https://upload.wikimedia.org/wikipedia/commons/6/69/Good_Food_Display_-_NCI_Visuals_Online.jpg'),
    # Myanmar flood
    ('myanmar', 'https://upload.wikimedia.org/wikipedia/commons/c/ca/Cyclone_Nargis_2008.jpg'),
]

# Also use FEMA category on Wikimedia - specifically ground level
FEMA_WIKIMEDIA_CATEGORIES = [
    ('fema_ground_flood', 'FEMA_-_Federal_Emergency_Management_Agency_flood_photographs'),
    ('flooding_streets', 'Floods_in_streets'),
    ('flood_rescue', 'Flood_rescue'),
    ('flood_boats', 'Rescue_boats_in_floods'),
]


def download_direct(url, dest_tag):
    """Download a single image from a direct URL."""
    dest_dir = os.path.join(DEST, dest_tag)
    os.makedirs(dest_dir, exist_ok=True)
    fname = url.split('/')[-1]
    fname = urllib.parse.unquote(fname).replace(' ', '_')
    fpath = os.path.join(dest_dir, fname)
    if os.path.exists(fpath):
        return True, 'exists'
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r, open(fpath, 'wb') as f:
            data = r.read()
            f.write(data)
        return True, f'{len(data)} bytes'
    except urllib.error.HTTPError as e:
        return False, f'HTTP {e.code}'
    except Exception as e:
        return False, str(e)


def get_wikimedia_category_images(category, limit=50):
    """Get image titles from a Wikimedia Commons category."""
    API = 'https://commons.wikimedia.org/w/api.php'
    h = {'User-Agent': 'FloodAI-Research/1.0 (academic)'}
    results = []
    cont = ''
    while len(results) < limit:
        url = (f'{API}?action=query&list=categorymembers'
               f'&cmtitle=Category:{urllib.parse.quote(category)}'
               f'&cmtype=file&cmlimit=50&format=json'
               + (f'&cmcontinue={urllib.parse.quote(cont)}' if cont else ''))
        try:
            req = urllib.request.Request(url, headers=h)
            data = json.loads(urllib.request.urlopen(req, timeout=20).read())
            for m in data.get('query', {}).get('categorymembers', []):
                if m['title'].lower().endswith(('.jpg', '.jpeg', '.png')):
                    results.append(m['title'])
            cont = data.get('continue', {}).get('cmcontinue', '')
            if not cont:
                break
            time.sleep(2.0)
        except Exception as e:
            print(f'  Category error: {e}')
            break
    return results[:limit]


def get_direct_url(title):
    API = 'https://commons.wikimedia.org/w/api.php'
    h = {'User-Agent': 'FloodAI-Research/1.0 (academic)'}
    enc = urllib.parse.quote(title)
    url = f'{API}?action=query&titles={enc}&prop=imageinfo&iiprop=url|mime&format=json'
    try:
        req = urllib.request.Request(url, headers=h)
        data = json.loads(urllib.request.urlopen(req, timeout=20).read())
        for _, page in data['query']['pages'].items():
            if 'imageinfo' in page:
                info = page['imageinfo'][0]
                if info.get('mime', '').startswith('image/'):
                    return info['url']
    except Exception:
        pass
    return None


if __name__ == '__main__':
    os.makedirs(DEST, exist_ok=True)
    total = 0

    print('=== Downloading direct URL images (Public Domain / CC) ===')
    for tag, url in DIRECT_URLS:
        ok, msg = download_direct(url, tag)
        status = 'OK' if ok else 'FAIL'
        fname = url.split('/')[-1][:50]
        print(f'  [{status}] {tag}/{fname}: {msg}')
        total += 1 if ok else 0
        time.sleep(1.5)

    print(f'\nDirect downloads: {total}')
    print('\n=== Downloading Wikimedia category images (with slow rate-limit) ===')
    for tag, cat in FEMA_WIKIMEDIA_CATEGORIES:
        print(f'\n[{tag}] Category: {cat}')
        dest_dir = os.path.join(DEST, tag)
        os.makedirs(dest_dir, exist_ok=True)
        titles = get_wikimedia_category_images(cat, limit=30)
        print(f'  {len(titles)} files found')
        cat_ok = 0
        for title in titles:
            fname = title.replace('File:', '').replace('/', '_').replace(' ', '_')
            fpath = os.path.join(dest_dir, fname)
            if os.path.exists(fpath):
                cat_ok += 1
                continue
            time.sleep(3.5)  # generous delay to avoid 429
            img_url = get_direct_url(title)
            if not img_url:
                continue
            time.sleep(2.0)
            ok, msg = download_direct(img_url, tag)
            if ok:
                cat_ok += 1
                print(f'  OK: {fname[:60]}')
            else:
                print(f'  Skip ({msg}): {title[:50]}')
        print(f'  Saved {cat_ok} from {tag}')
        total += cat_ok

    print(f'\nTotal images: {total}')
