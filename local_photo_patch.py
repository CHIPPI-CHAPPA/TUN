
# Use browser-captured photos from each exact venue/landmark source page.
def fetch(it):
    code={'ДОСТОПРИМЕЧАТЕЛЬНОСТИ':'a','ОТЕЛИ':'h','КАФЕ И РЕСТОРАНЫ':'r'}[it.section]
    p=Path('preset')/f'{code}{int(it.number):02d}.jpg'
    if p.exists():
        it.photo_path=p
        it.photo_url=''
        it.source_page=SOURCE_PAGES.get(it.name,'')
        it.source_title=f'Exact source page for {it.name}'
        it.source_domain=dom(it.source_page)
        it.status='exact-browser-capture'
    else:
        it.status='MISSING'

if __name__=='__main__': raise SystemExit(main())
