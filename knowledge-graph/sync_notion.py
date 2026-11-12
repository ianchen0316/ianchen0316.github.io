#!/usr/bin/env python3
"""Read-only Notion hierarchy synchronizer. Publishes titles/URLs, never page bodies."""
import datetime, json, os, pathlib, re, time, urllib.error, urllib.parse, urllib.request
BASE=pathlib.Path(__file__).resolve().parent
TOKEN=os.environ.get("NOTION_TOKEN")
if not TOKEN: raise SystemExit("NOTION_TOKEN secret missing")
ROOTS=[("ml","963f7995-6cee-49e0-a857-07ca6e3a4853"),("llm","3f275fde-b6eb-809c-8ff0-de72173259bb"),("agents","28f75fde-b6eb-8048-9783-cf7af2337650"),("kg","19e75fde-b6eb-80bc-bb83-f5c1c80a6e09")]
MAX_PAGES=int(os.environ.get("NOTION_MAX_PAGES","100"))
MAX_DEPTH=int(os.environ.get("NOTION_MAX_DEPTH","2"))
def fetch(path):
  for attempt in range(5):
    req=urllib.request.Request("https://api.notion.com/v1"+path,headers={"Authorization":"Bearer "+TOKEN,"Notion-Version":"2022-06-28"})
    try:
      with urllib.request.urlopen(req,timeout=25) as res:return json.load(res)
    except urllib.error.HTTPError as e:
      if e.code in (429,500,502,503,504) and attempt<4:
        time.sleep(int(e.headers.get("Retry-After","2")) if e.code==429 else 2**attempt)
        continue
      raise
def children(page):
  items=[]; cursor=None
  while True:
    suffix="?page_size=100"+("&start_cursor="+urllib.parse.quote(cursor) if cursor else "")
    batch=fetch("/blocks/"+page+"/children"+suffix)
    items+=batch["results"];cursor=batch.get("next_cursor")
    if not batch.get("has_more"):return items
def label(rich):return "".join(x.get("plain_text",x.get("text",{}).get("content","")) for x in rich).strip()
def url(x):return "https://www.notion.so/"+x.replace("-","")
html_path=BASE/"index.html";html=html_path.read_text(encoding="utf-8")
match=re.search(r'<script id="data" type="application/json">(.*?)</script>',html,re.S)
if not match:raise RuntimeError("Embedded graph JSON marker missing")
graph=json.loads(match.group(1));existing={n["id"]:n for n in graph["nodes"]}
seen=set();warnings=[]
def add(id,title,kind,parent,source):
  if id in existing:return
  existing[id]={"id":id,"label":title,"type":kind,"parent":parent,"url":source,"description":"Notion page or section discovered during the latest structural sync; semantic description not yet reviewed.","keywords":title.lower().split()[:8],"review_status":"unreviewed","source_pages":[{"title":"Notion source","url":source}],"origin":"notion_api","extraction_method":"notion_structure"}
def walk(page,parent,depth):
  if page in seen or depth>MAX_DEPTH or len(seen)>=MAX_PAGES:return
  seen.add(page);current=parent
  try:blocks=children(page)
  except Exception as e:
    warnings.append(f"{parent}: {type(e).__name__}");return
  for b in blocks:
    kind=b["type"];bid=b["id"]
    if kind in ("heading_1","heading_2","heading_3"):
      text=label(b[kind].get("rich_text",[]))
      if text:
        current="notion-heading-"+bid
        add(current,text,"topic",parent,url(page)+"#"+bid.replace("-",""))
    elif kind=="child_page":
      name=b[kind].get("title","Untitled");node="notion-page-"+bid
      add(node,name,"note",current,url(bid))
      if depth<MAX_DEPTH:walk(bid,node,depth+1)
for root,page in ROOTS:walk(page,root,0)
graph["nodes"]=list(existing.values())
graph["metadata"]["last_synced_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
graph["metadata"]["sync_status"]="Notion page/heading hierarchy; no full page contents"
serialized=json.dumps(graph,ensure_ascii=False).replace("<","\\u003c")
html=html[:match.start(1)]+serialized+html[match.end(1):]
html_path.write_text(html,encoding="utf-8")
print(f"Synced {len(seen)} Notion pages/blocks; {len(existing)} graph nodes; warnings: {warnings}")
