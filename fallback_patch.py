
# Final strict-name fallback. This definition overrides the earlier fetch().
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
        cc=commons(it.query,50)
        print('  commons candidates',len(cc),flush=True)
        for x in cc:
            label=norm(x.get('title','')); matches=sum(1 for t in req if t in label)
            if matches < 1: continue
            if dl(x.get('image_url',''),path,x.get('page_url','')):
                it.photo_path=path; it.photo_url=x.get('image_url',''); it.source_page=x.get('page_url',''); it.source_title=x.get('title',''); it.source_domain=dom(it.source_page); it.status='exact-commons-search'; return
        search_query=it.query
        req=_required(it.query)
    else:
        search_query=f'"{it.name}" {it.city} Vietnam photos'
        req=_required(it.name)
    bc=_bing_candidates(search_query,120)
    print('  bing candidates',len(bc),'required',req,flush=True)
    for iu,tu,pu,title,text in bc:
        matches=sum(1 for t in req if t in text)
        if matches < 1: continue
        if any(x in text for x in ('porn','xxx','adult','escort')): continue
        for u in (iu,tu):
            if u and dl(u,path,pu):
                it.photo_path=path; it.photo_url=u; it.source_page=pu or u; it.source_title=title; it.source_domain=dom(it.source_page); it.status='exact-bing'; return
    it.status='MISSING'

if __name__=='__main__': raise SystemExit(main())
