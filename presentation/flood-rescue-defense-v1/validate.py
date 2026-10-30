#!/usr/bin/env python3
"""Browser checks and PDF export for the local, offline presentation."""
from pathlib import Path
import argparse
import base64
import json
import re
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--browser', help='Optional Chromium/headless-shell executable')
args=parser.parse_args()
out=HERE/'checks'
out.mkdir(exist_ok=True)
errors=[]
requests=[]
with sync_playwright() as p:
    kw={'headless':True,'args':['--no-sandbox']}
    if args.browser:
        kw['executable_path']=args.browser
    browser=p.chromium.launch(**kw)
    page=browser.new_page(viewport={'width':1600,'height':900},device_scale_factor=1)
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda req:requests.append(req.url))
    page.goto((HERE/'index.html').as_uri(),wait_until='load')
    page.evaluate('document.fonts.ready')
    count=page.evaluate('deck.count')
    assert count==28
    checks=[]
    for i in range(count):
        page.evaluate('(i)=>deck.go(i)',i)
        page.wait_for_timeout(200)
        result=page.evaluate('''()=>{
          const s=document.querySelector('.slide.on'), take=s.querySelector('.take'), foot=s.querySelector('.foot');
          const scale=document.querySelector('#stage').getBoundingClientRect().width/1600;
          const sr=s.getBoundingClientRect(), limit=(take||foot).getBoundingClientRect().top-8*scale;
          let overflow=[];
          if(!s.classList.contains('cover')){
            for(const el of s.querySelectorAll('.content > *, .content .card, .content p, .content h3')){
              let r=el.getBoundingClientRect();
              if(r.bottom>limit+2*scale||r.right>sr.right-65*scale||r.left<sr.left+65*scale)
                overflow.push({tag:el.tagName,cls:el.className,text:el.textContent.slice(0,95),bottom:r.bottom,limit});
            }
          }
          return {title:s.dataset.title,overflow,visibleSlides:document.querySelectorAll('.slide.on').length,
            font:document.fonts.check('26px DeckSans'),notes:!!s.querySelector('.speaker-note').textContent};
        }''')
        checks.append(result)
        page.screenshot(path=str(out/f'slide-{i+1:02}.png'),animations='disabled')
    page.evaluate('deck.go(0)')
    page.keyboard.press('ArrowRight')
    assert page.locator('.slide.on').get_attribute('id')=='s2'
    page.keyboard.press('Home')
    assert page.locator('.slide.on').get_attribute('id')=='s1'
    page.keyboard.press('ArrowLeft')
    assert page.locator('.slide.on').get_attribute('id')=='s1'
    page.keyboard.press('n')
    assert page.locator('#notes').is_visible()
    page.keyboard.press('Escape')
    assert not page.locator('#notes').is_visible()
    page.keyboard.press('o')
    assert page.locator('#overview').is_visible()
    page.locator('#overview .items button').nth(6).click()
    assert page.locator('.slide.on').get_attribute('id')=='s7'
    assert not page.locator('#overview').is_visible()
    page.locator('#jump').select_option('18')
    assert page.locator('.slide.on').get_attribute('id')=='s19'
    page.locator('#next').click()
    assert page.locator('.slide.on').get_attribute('id')=='s20'
    page.keyboard.press('End')
    page.keyboard.press('ArrowRight')
    assert page.locator('.slide.on').get_attribute('id')=='s28'
    page.goto((HERE/'index.html').as_uri()+'#5',wait_until='load')
    assert page.locator('.slide.on').get_attribute('id')=='s5'
    page.pdf(path=str(HERE/'slides.pdf'),prefer_css_page_size=True,print_background=True)
    # Responsive fit, including no horizontal page overflow. Slides retain 16:9.
    responsive=[]
    for width,height in [(1280,720),(1920,1080),(390,844)]:
        page.set_viewport_size({'width':width,'height':height})
        page.wait_for_timeout(100)
        r=page.evaluate('''()=>{let r=document.querySelector('#stage').getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,docWidth:document.documentElement.scrollWidth};}''')
        assert r['x']>=-1 and r['y']>=-1 and r['x']+r['w']<=width+1 and r['y']+r['h']<=height+1
        assert r['docWidth']<=width
        responsive.append({'viewport':[width,height],**r})
    page.screenshot(path=str(out/'mobile.png'))
    # A browser-rendered contact sheet avoids extra image-library dependencies.
    tiles=[]
    for i in range(count):
        data=base64.b64encode((out/f'slide-{i+1:02}.png').read_bytes()).decode()
        tiles.append(f'<div><img src="data:image/png;base64,{data}"><span>{i+1:02}</span></div>')
    sheet=browser.new_page(viewport={'width':1600,'height':1750},device_scale_factor=1)
    sheet.set_content('<style>*{box-sizing:border-box}body{margin:0;padding:10px;background:#101B2D;display:grid;grid-template-columns:repeat(4,1fr);gap:10px}div{position:relative}img{width:100%;display:block}span{position:absolute;bottom:4px;right:4px;background:#101B2D;color:white;font:14px Arial;padding:3px 5px}</style>'+''.join(tiles))
    sheet.screenshot(path=str(out/'contact-sheet.png'),full_page=True)
    browser.close()

web=[u for u in requests if re.match(r'https?://',u)]
report={'slides':count,'errors':errors,'external_requests':web,'layout':checks,'responsive':responsive,
        'navigation':'keyboard, boundaries, menu, selector, next button, hash reload, notes, Escape passed',
        'pdf':'../slides.pdf','screenshots':'slide-01.png through slide-28.png',
        'pass':not errors and not web and not any(c['overflow'] for c in checks)}
(out/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'pass':report['pass'],'errors':errors,'external_requests':web,'layout_issues':[(i+1,c['overflow']) for i,c in enumerate(checks) if c['overflow']]},ensure_ascii=False))
