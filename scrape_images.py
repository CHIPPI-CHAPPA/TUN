from __future__ import annotations
import asyncio, csv, json, re, unicodedata
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image, ImageStat
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

OUT=Path('preset'); OUT.mkdir(exist_ok=True)
TMP=OUT/'tmp'; TMP.mkdir(exist_ok=True)
DATA=json.loads(Path('vietnam_data.json').read_text(encoding='utf-8'))
SOURCES=json.loads(Path('source_pages.json').read_text(encoding='utf-8'))
SOURCES['Trang An Riverside Garden']='https://www.happycow.net/reviews/tam-coc-ngo-dong-homestay-and-vegan-restaurant-ninh-binh-327356'
CODES={'ДОСТОПРИМЕЧАТЕЛЬНОСТИ':'a','ОТЕЛИ':'h','КАФЕ И РЕСТОРАНЫ':'r'}
BAD=('logo','icon','avatar','sprite','flag','map','advert','banner-ad','payment','badge','qr')
STOP={'hotel','spa','boutique','resort','restaurant','cafe','coffee','garden','original','grand','center','house','villa','beach','hanoi','hue','hoian','hoi','ninh','binh','vietnam','danang','nang','the','and','bar','de','la'}

def norm(s):
    s=unicodedata.normalize('NFKD',str(s)); s=''.join(c for c in s if not unicodedata.combining(c)); return re.sub(r'[^a-z0-9]+',' ',s.lower()).strip()
def tokens(s): return [x for x in norm(s).split() if len(x)>=3 and x not in STOP]
def valid_image(path):
    try:
        im=Image.open(path).convert('RGB')
        if im.width<500 or im.height<280 or im.width*im.height<220000:return False
        st=ImageStat.Stat(im.resize((80,80)))
        return max(st.var)>60
    except Exception:return False
def convert(src,dst):
    im=Image.open(src).convert('RGB')
    if im.width>1800 or im.height>1300: im.thumbnail((1800,1300),Image.Resampling.LANCZOS)
    im.save(dst,'JPEG',quality=86,optimize=True,progressive=True)

async def inspect_img(el, req):
    try:
        box=await el.bounding_box()
        if not box or box['width']<180 or box['height']<120:return None
        p=await el.evaluate("""e=>({
          nw:e.naturalWidth||0,nh:e.naturalHeight||0,
          alt:[e.alt,e.title,e.getAttribute('aria-label'),e.currentSrc,e.src,
            e.parentElement?.innerText,e.parentElement?.parentElement?.innerText].filter(Boolean).join(' ').slice(0,1800)
        })""")
        if p['nw']<300 or p['nh']<200:return None
        text=norm(p['alt'])
        if any(x in text for x in BAD):return None
        match=sum(1 for t in req if t in text)
        area=box['width']*box['height']; natural=min(p['nw']*p['nh'],5000000)
        score=area+natural*.06+match*1500000
        return score,el,text
    except Exception:return None

async def inspect_backgrounds(page,req):
    try:
        ids=await page.evaluate("""()=>{
          let out=[],n=0;
          for(const e of document.querySelectorAll('main *,article *,section *,div')){
            const s=getComputedStyle(e),r=e.getBoundingClientRect();
            if(s.backgroundImage && s.backgroundImage!=='none' && r.width>=400 && r.height>=220){
              const id='capbg'+(++n);e.dataset.captureBg=id;
              out.push({id,w:r.width,h:r.height,text:(e.innerText||'').slice(0,1200),bg:s.backgroundImage});
              if(out.length>=80)break;
            }
          }return out;
        }""")
        out=[]
        for x in ids:
            text=norm((x.get('text') or '')+' '+(x.get('bg') or ''))
            if any(b in text for b in BAD):continue
            match=sum(1 for t in req if t in text)
            el=page.locator(f'[data-capture-bg="{x["id"]}"]').first
            score=x['w']*x['h']+match*1500000
            out.append((score,el,text))
        return out
    except Exception:return []

async def capture_one(context,item,sem):
    async with sem:
        code=CODES[item['section']]; num=int(item['number']); dst=OUT/f'{code}{num:02d}.jpg'; url=SOURCES.get(item['name'])
        if dst.exists() and valid_image(dst):return [item['name'],'cached',url,'']
        if not url:return [item['name'],'missing-source','','']
        req=tokens(item['name'])
        page=await context.new_page()
        try:
            await page.goto(url,wait_until='domcontentloaded',timeout=45000)
            await page.wait_for_timeout(1800)
            try:
                height=await page.evaluate('document.documentElement.scrollHeight')
                for y in range(0,min(int(height),7000),900):
                    await page.evaluate(f'window.scrollTo(0,{y})'); await page.wait_for_timeout(120)
                await page.evaluate('window.scrollTo(0,0)')
            except Exception:pass
            candidates=[]
            for el in await page.query_selector_all('img'):
                z=await inspect_img(el,req)
                if z:candidates.append(z)
            candidates+=await inspect_backgrounds(page,req)
            candidates.sort(key=lambda x:x[0],reverse=True)
            for rank,(score,el,text) in enumerate(candidates[:15]):
                tmp=TMP/f'{code}{num:02d}_{rank}.png'
                try:
                    await el.screenshot(path=str(tmp),timeout=20000,animations='disabled')
                    if valid_image(tmp):
                        convert(tmp,dst)
                        return [item['name'],'ok',page.url,text[:180]]
                except Exception:pass
                finally:tmp.unlink(missing_ok=True)
            # Last-resort real browser capture from the exact venue page.
            tmp=TMP/f'{code}{num:02d}_page.png'
            await page.screenshot(path=str(tmp),full_page=False)
            if valid_image(tmp):
                convert(tmp,dst)
                return [item['name'],'page-capture',page.url,'exact source page viewport']
            return [item['name'],'no-image',page.url,'']
        except PlaywrightTimeout:
            return [item['name'],'timeout',url,'']
        except Exception as e:
            return [item['name'],'error',url,str(e)[:160]]
        finally:
            await page.close()

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=['--disable-blink-features=AutomationControlled','--no-sandbox'])
        context=await browser.new_context(viewport={'width':1440,'height':1000},locale='en-GB',user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36')
        sem=asyncio.Semaphore(4)
        rows=await asyncio.gather(*(capture_one(context,x,sem) for x in DATA))
        await browser.close()
    with open(OUT/'capture_report.csv','w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['name','status','url','detail']);w.writerows(rows)
    for r in rows:print(' | '.join(r),flush=True)
    good=sum(1 for x in DATA if (OUT/f"{CODES[x['section']]}{int(x['number']):02d}.jpg").exists())
    print('CAPTURED',good,'OF',len(DATA),flush=True)
    return 0 if good==len(DATA) else 2

if __name__=='__main__':raise SystemExit(asyncio.run(main()))
