
# Exact-source override: photos must be for the named landmark, hotel or venue.
from urllib.parse import urljoin

SOURCE_PAGES = json.loads(Path('source_pages.json').read_text(encoding='utf-8'))
SOURCE_PAGES['Trang An Riverside Garden'] = 'https://www.happycow.net/reviews/tam-coc-ngo-dong-homestay-and-vegan-restaurant-ninh-binh-327356'

EXCLUDE = {'hotel','restaurant','cafe','coffee','boutique','resort','spa','garden','original','grand','center','house','villa','beach','hanoi','hue','hoian','hoi','ninh','binh','vietnam','danang','nang','the','and','bar','de','la'}

def _required(text):
    return [x for x in norm(text).split() if len(x) >= 3 and x not in EXCLUDE]

def _json_images(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in ('image', 'images', 'thumbnailurl', 'contenturl'):
                if isinstance(v, str): out.append((v, str(obj.get('name') or obj.get('caption') or 'json image'), 8))
                elif isinstance(v, list):
                    for z in v:
                        if isinstance(z, str): out.append((z, 'json image', 8))
                        elif isinstance(z, dict): _json_images(z, out)
                elif isinstance(v, dict): _json_images(v, out)
            else: _json_images(v, out)
    elif isinstance(obj, list):
        for x in obj: _json_images(x, out)

def _page_image_candidates(page_url, it):
    try:
        r = S.get(page_url, timeout=TIMEOUT, allow_redirects=True, headers={
            'User-Agent': UA, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9,vi;q=0.7'})
        if r.status_code >= 400 or len(r.content) < 500: return [], '', page_url
    except requests.RequestException: return [], '', page_url
    final_url = r.url; soup = BeautifulSoup(r.text, 'html.parser')
    title = soup.title.get_text(' ', strip=True) if soup.title else it.name
    candidates = []
    for selector, bonus in [('meta[property="og:image:secure_url"]',35),('meta[property="og:image"]',32),('meta[name="twitter:image"]',28),('meta[property="twitter:image"]',28),('link[rel="image_src"]',25)]:
        for tag in soup.select(selector):
            u = tag.get('content') or tag.get('href')
            if u: candidates.append((urljoin(final_url,u.strip()),title,bonus))
    for script in soup.select('script[type="application/ld+json"]'):
        try: _json_images(json.loads(script.get_text()), candidates)
        except Exception: pass
    for a in soup.select('.fullImageLink a, a.internal, a.image'):
        u=a.get('href')
        if u: candidates.append((urljoin(final_url,u),a.get('title') or title,40))
    for img in soup.find_all('img'):
        alt=' '.join(filter(None,[img.get('alt'),img.get('title'),img.get('aria-label')]))
        srcs=[]
        for key in ('data-original','data-src','data-lazy-src','data-image','src'):
            if img.get(key): srcs.append(img.get(key))
        for key in ('srcset','data-srcset'):
            if img.get(key): srcs.extend(reversed([p.strip().split(' ')[0] for p in img.get(key).split(',') if p.strip()]))
        for u in srcs:
            if u and not u.startswith('data:'): candidates.append((urljoin(final_url,u.strip()),alt or title,4))
    req=_required(it.name); seen=set(); scored=[]
    for u,label,bonus in candidates:
        if not u or u in seen: continue
        seen.add(u); text=norm(' '.join([label or '',u,title])); matches=sum(1 for t in req if t in text)
        if any(x in text for x in ('logo','icon','avatar','sprite','map','flag','banner-ad','advert')): continue
        scored.append((bonus+matches*15+(2 if dom(u)==dom(final_url) else 0),u,label or title))
    scored.sort(key=lambda x:x[0],reverse=True)
    return scored,title,final_url

def _bing_candidates(query, limit=80):
    try:
        r=S.get('https://www.bing.com/images/search',params={'q':query,'form':'HDRSC2','first':1},timeout=TIMEOUT)
        soup=BeautifulSoup(r.text,'html.parser')
    except requests.RequestException: return []
    out=[]
    for a in soup.select('a.iusc')[:limit]:
        try: m=json.loads(html.unescape(a.get('m','')))
        except Exception: continue
        iu=m.get('murl',''); tu=m.get('turl',''); pu=m.get('purl',''); title=m.get('t','') or a.get('aria-label','')
        text=norm(' '.join([title,pu,iu]))
        if not iu or any(x in text for x in ('ai generated','midjourney','dall e','stable diffusion','freepik','pinterest','porn','xxx')): continue
        out.append((iu,tu,pu,title,text))
    return out

def fetch(it):
    path=IMG/f"{norm(it.section)[:3]}_{it.number:02d}_{fname(it.name)}.jpg"
    page=SOURCE_PAGES.get(it.name)
    if page:
        candidates,page_title,final_page=_page_image_candidates(page,it)
        for score,image_url,label in candidates[:60]:
            if dl(image_url,path,final_page):
                it.photo_path=path; it.photo_url=image_url; it.source_page=final_page; it.source_title=label or page_title; it.source_domain=dom(final_page); it.status='exact-source-page'; return
    if it.section=='ДОСТОПРИМЕЧАТЕЛЬНОСТИ':
        req=_required(it.query)
        for x in commons(it.query,40):
            label=norm(x.get('title','')); matches=sum(1 for t in req if t in label)
            if matches < max(1,min(2,len(req))): continue
            if dl(x.get('image_url',''),path,x.get('page_url','')):
                it.photo_path=path; it.photo_url=x.get('image_url',''); it.source_page=x.get('page_url',''); it.source_title=x.get('title',''); it.source_domain=dom(it.source_page); it.status='exact-commons-search'; return
    else:
        req=_required(it.name); need=max(1,min(2,len(req)))
        city_tokens=[x for x in norm(it.city).split() if len(x)>=3]
        for iu,tu,pu,title,text in _bing_candidates(f'"{it.name}" {it.city} Vietnam photos',100):
            matches=sum(1 for t in req if t in text)
            city_ok=not city_tokens or any(t in text for t in city_tokens) or 'vietnam' in text
            if matches < need or not city_ok: continue
            for u in (iu,tu):
                if u and dl(u,path,pu):
                    it.photo_path=path; it.photo_url=u; it.source_page=pu or u; it.source_title=title; it.source_domain=dom(it.source_page); it.status='exact-bing'; return
    it.status='MISSING'

if __name__=='__main__': raise SystemExit(main())
