
# Exact-source override: every photo must come from the mapped venue/landmark page.
from urllib.parse import urljoin

SOURCE_PAGES = json.loads(Path('source_pages.json').read_text(encoding='utf-8'))
SOURCE_PAGES['Trang An Riverside Garden'] = 'https://www.happycow.net/reviews/tam-coc-ngo-dong-homestay-and-vegan-restaurant-ninh-binh-327356'

def _json_images(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in ('image', 'images', 'thumbnailurl', 'contenturl'):
                if isinstance(v, str):
                    out.append((v, str(obj.get('name') or obj.get('caption') or 'json image'), 5))
                elif isinstance(v, list):
                    for z in v:
                        if isinstance(z, str): out.append((z, 'json image', 5))
                        elif isinstance(z, dict): _json_images(z, out)
                elif isinstance(v, dict): _json_images(v, out)
            else:
                _json_images(v, out)
    elif isinstance(obj, list):
        for x in obj: _json_images(x, out)

def _page_image_candidates(page_url, it):
    try:
        r = S.get(page_url, timeout=TIMEOUT, allow_redirects=True, headers={
            'User-Agent': UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9,vi;q=0.7'
        })
        if r.status_code >= 400 or len(r.content) < 500:
            return [], '', page_url
    except requests.RequestException:
        return [], '', page_url
    final_url = r.url
    soup = BeautifulSoup(r.text, 'html.parser')
    title = (soup.title.get_text(' ', strip=True) if soup.title else it.name)
    candidates = []
    meta_specs = [
        ('meta[property="og:image:secure_url"]', 30), ('meta[property="og:image"]', 28),
        ('meta[name="twitter:image"]', 25), ('meta[property="twitter:image"]', 25),
        ('link[rel="image_src"]', 20)
    ]
    for selector, bonus in meta_specs:
        for tag in soup.select(selector):
            u = tag.get('content') or tag.get('href')
            if u: candidates.append((urljoin(final_url, u.strip()), title, bonus))
    for script in soup.select('script[type="application/ld+json"]'):
        try: _json_images(json.loads(script.get_text()), candidates)
        except Exception: pass
    for a in soup.select('.fullImageLink a, a.internal, a.image'):
        u = a.get('href')
        if u: candidates.append((urljoin(final_url, u), a.get('title') or title, 35))
    for img in soup.find_all('img'):
        alt = ' '.join(filter(None, [img.get('alt'), img.get('title'), img.get('aria-label')]))
        srcs = []
        for key in ('data-original', 'data-src', 'data-lazy-src', 'data-image', 'src'):
            if img.get(key): srcs.append(img.get(key))
        for key in ('srcset', 'data-srcset'):
            if img.get(key):
                parts = [p.strip().split(' ')[0] for p in img.get(key).split(',') if p.strip()]
                srcs.extend(reversed(parts))
        try:
            w = int(re.sub(r'\D', '', str(img.get('width') or '0')) or 0)
            h = int(re.sub(r'\D', '', str(img.get('height') or '0')) or 0)
            dim_bonus = 4 if w >= 700 or h >= 500 else 0
        except Exception: dim_bonus = 0
        for u in srcs:
            if u and not u.startswith('data:'):
                candidates.append((urljoin(final_url, u.strip()), alt or title, 2 + dim_bonus))
    req = [x for x in toks(it.name) if x not in ('hotel','restaurant','cafe','coffee','boutique','resort','spa','garden','original')]
    if not req: req = toks(it.name)
    seen = set(); scored = []
    for u, label, bonus in candidates:
        if not u or u in seen: continue
        seen.add(u)
        text = norm(' '.join([label or '', u, title]))
        matches = sum(1 for t in req if t in text)
        bad = any(x in text for x in ('logo','icon','avatar','sprite','map','flag','banner-ad','advert'))
        if bad: continue
        score = bonus + matches * 12
        if dom(u) == dom(final_url): score += 2
        scored.append((score, u, label or title))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored, title, final_url

def fetch(it):
    path = IMG / f"{norm(it.section)[:3]}_{it.number:02d}_{fname(it.name)}.jpg"
    page = SOURCE_PAGES.get(it.name)
    if page:
        candidates, page_title, final_page = _page_image_candidates(page, it)
        for score, image_url, label in candidates[:50]:
            if dl(image_url, path, final_page):
                it.photo_path = path
                it.photo_url = image_url
                it.source_page = final_page
                it.source_title = label or page_title
                it.source_domain = dom(final_page)
                it.status = 'exact-source-page'
                return
    # Strict attraction-only fallback to Wikimedia search. Never use a regional
    # or generic fallback for a hotel or restaurant.
    if it.section == 'ДОСТОПРИМЕЧАТЕЛЬНОСТИ':
        for x in commons(it.query, 30):
            label = norm(x.get('title',''))
            req = toks(it.name)
            if sum(1 for t in req if t in label) < max(1, min(2, len(req))):
                continue
            if dl(x.get('image_url',''), path, x.get('page_url','')):
                it.photo_path = path
                it.photo_url = x.get('image_url','')
                it.source_page = x.get('page_url','')
                it.source_title = x.get('title','')
                it.source_domain = dom(it.source_page)
                it.status = 'exact-commons-search'
                return
    it.status = 'MISSING'

if __name__ == '__main__':
    raise SystemExit(main())
