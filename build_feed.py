#!/usr/bin/env python3
"""Build a public-only, source-linked Morning Three feed. No AI keys or personal data."""
import datetime as dt, email.utils, json, pathlib, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

ROOT=pathlib.Path(__file__).parent
NOW=dt.datetime.now(dt.timezone.utc)
QUERIES={
 'Technology':'technology innovation when:1d',
 'AI':'artificial intelligence research when:1d',
 'Culture':'culture arts entertainment when:1d',
 'World':'world international affairs when:1d',
}

def read_category(category, query):
    url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':query,'hl':'en-US','gl':'US','ceid':'US:en'})
    request=urllib.request.Request(url,headers={'User-Agent':'TheEditNews/1.0 (personal news reader)'})
    with urllib.request.urlopen(request,timeout=25) as response:
        root=ET.fromstring(response.read())
    found=[]
    for item in root.findall('.//item'):
        title=(item.findtext('title') or '').strip()
        link=(item.findtext('link') or '').strip()
        source=(item.findtext('source') or '').strip() or 'Google News'
        raw=item.findtext('pubDate') or ''
        try: published=email.utils.parsedate_to_datetime(raw).astimezone(dt.timezone.utc)
        except (TypeError,ValueError): continue
        if not (NOW-dt.timedelta(hours=12) <= published <= NOW) or not link.startswith('https://'):continue
        if title.endswith(' - '+source):title=title[:-(len(source)+3)]
        found.append({'title':title,'url':link,'source':source,'publishedAt':published.isoformat().replace('+00:00','Z'),'category':category,'whyItMatters':f'A timely {category.lower()} story worth reading for context and perspective. Open the original reporting to assess its significance.'})
    return sorted(found,key=lambda x:x['publishedAt'],reverse=True)

def main():
    # Generate only at 6 AM Pacific on scheduled runs; manual dispatch can run any time.
    buckets={}
    for category,query in QUERIES.items():
        try: buckets[category]=read_category(category,query)
        except Exception as exc:
            print(f'Could not retrieve {category}: {exc}')
            buckets[category]=[]
    # Prefer one tech or AI, one world, one culture; rotate AI/technology by date.
    tech_order=['AI','Technology'] if NOW.day%2 else ['Technology','AI']
    selection=[];seen=set()
    for choices in (tech_order,['World'],['Culture']):
        for category in choices:
            for item in buckets[category]:
                key=re.sub(r'\W+','',item['title'].lower())[:90]
                if key and key not in seen:
                    selection.append(item);seen.add(key);break
            if len(selection)==len(seen) and selection and selection[-1]['category']==category:break
    if len(selection)!=3:
        raise SystemExit('Fewer than three qualifying articles. Preserving previous edition; no stale or invented articles.')
    edition={'generatedAt':NOW.isoformat().replace('+00:00','Z'),'articles':selection}
    (ROOT/'docs').mkdir(exist_ok=True)
    (ROOT/'docs'/'edition.json').write_text(json.dumps(edition,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Created edition',edition['generatedAt'],[x['category'] for x in selection])
if __name__=='__main__':main()
