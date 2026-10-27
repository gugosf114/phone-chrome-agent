#!/usr/bin/env python3
# marks.py — "set of marks": take a phone screenshot + the accessibility dump, draw numbered
# boxes on every clickable/labelled element, and print a numbered list with tap coordinates.
# This is the light, accurate version of an OmniParser-style screen reader: it uses Android's
# OWN accessibility tree (the real UI element list) instead of guessing elements from pixels.
#   marks.py annotate <shot.png> <window_dump.xml> <out.png> <list.json>
import sys, re, json
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

def parse_bounds(b):
    m = re.findall(r'-?\d+', b or '')
    if len(m) != 4: return None
    x1,y1,x2,y2 = map(int, m)
    return x1,y1,x2,y2

def main():
    shot, xml, out, listout = sys.argv[1:5]
    tree = ET.parse(xml); root = tree.getroot()
    items = []
    for n in root.iter('node'):
        a = n.attrib
        bounds = parse_bounds(a.get('bounds'))
        if not bounds: continue
        x1,y1,x2,y2 = bounds
        w,h = x2-x1, y2-y1
        if w < 12 or h < 12 or w > 4000 or h > 4000: continue
        text = (a.get('text') or '').strip()
        desc = (a.get('content-desc') or '').strip()
        clickable = a.get('clickable') == 'true'
        label = text or desc
        # keep clickable things, or anything with a visible label
        if not (clickable or label): continue
        items.append({'x1':x1,'y1':y1,'x2':x2,'y2':y2,'cx':(x1+x2)//2,'cy':(y1+y2)//2,
                      'clickable':clickable,'t':(label[:40] or '['+(a.get('class') or '').split('.')[-1]+']')})
    # de-dup near-identical boxes, prefer clickable
    items.sort(key=lambda i:(i['cy'],i['cx']))
    dedup=[]
    for it in items:
        if any(abs(it['cx']-d['cx'])<8 and abs(it['cy']-d['cy'])<8 for d in dedup): continue
        dedup.append(it)
    im = Image.open(shot).convert('RGB'); d = ImageDraw.Draw(im)
    try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 34)
    except Exception: font = ImageFont.load_default()
    out_list=[]
    for i,it in enumerate(dedup, 1):
        col = (230,20,20) if it['clickable'] else (30,120,220)
        d.rectangle([it['x1'],it['y1'],it['x2'],it['y2']], outline=col, width=3)
        tag=str(i)
        d.rectangle([it['x1'],it['y1'],it['x1']+len(tag)*22+8,it['y1']+40], fill=col)
        d.text((it['x1']+5,it['y1']+2), tag, fill=(255,255,255), font=font)
        out_list.append({'n':i,'t':it['t'],'cx':it['cx'],'cy':it['cy'],'click':it['clickable']})
    im.save(out)
    json.dump(out_list, open(listout,'w'))
    print(f"{len(out_list)} elements marked")
    for it in out_list[:40]:
        print(f"  {it['n']:>3}{'*' if it['click'] else ' '} ({it['cx']},{it['cy']})  {it['t']}")

if __name__=='__main__': main()
