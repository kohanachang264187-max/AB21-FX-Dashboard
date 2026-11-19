#!/usr/bin/env python3
"""Sync only allowlisted research-only H1 bars from a private repo via a read-only token.
Requires AB21_SOURCE_TOKEN; never copies private files other than 21 sanitized CSVs.
"""
import base64,csv,io,json,os,sys,urllib.request
from datetime import datetime,timezone
from pathlib import Path

PAIRS="USDJPY EURJPY GBPJPY AUDJPY NZDJPY CADJPY CHFJPY EURUSD GBPUSD AUDUSD NZDUSD USDCAD USDCHF EURGBP EURAUD EURNZD EURCHF GBPAUD GBPCHF AUDNZD AUDCHF".split()
FIELDS=["Pair","StartUTC","EndUTC","Open","High","Low","Close","Status"]
SOURCE="kohanachang264187-max/AB21-FX-Trading-System"
REF=os.environ.get("AB21_SOURCE_REF","feature/ab21-dashboard-v2-20261118")
ROOT=Path(__file__).resolve().parents[1]
def fetch(pair,token):
    url=f"https://api.github.com/repos/{SOURCE}/contents/research_data/fx_sessions/H1/{pair}.csv?ref={REF}"
    req=urllib.request.Request(url,headers={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json","User-Agent":"AB21-research-public-sync"})
    with urllib.request.urlopen(req,timeout=30) as res:obj=json.load(res)
    return base64.b64decode(obj["content"]).decode("utf-8-sig")
def validate(pair,raw):
    reader=csv.DictReader(io.StringIO(raw))
    if not set(FIELDS).issubset(reader.fieldnames or []):raise ValueError(f"{pair}: columns")
    rows=list(reader)
    if not rows:raise ValueError(f"{pair}: empty")
    previous=None
    for r in rows:
        if r["Pair"]!=pair or r["Status"]!="PROVISIONAL_NOT_TRADEABLE":raise ValueError(f"{pair}: invalid research status")
        start=datetime.fromisoformat(r["StartUTC"].replace("Z","+00:00"))
        end=datetime.fromisoformat(r["EndUTC"].replace("Z","+00:00"))
        if start.tzinfo is None or end.tzinfo is None or start>=end or (previous is not None and end<=previous):raise ValueError(f"{pair}: timestamps")
        previous=end
        prices=[float(r[k]) for k in ("Open","High","Low","Close")]
        if min(prices)<=0 or prices[1]<max(prices[0],prices[2],prices[3]) or prices[2]>min(prices[0],prices[1],prices[3]):raise ValueError(f"{pair}: OHLC")
    return rows[-2500:],previous
def main():
    token=os.environ.get("AB21_SOURCE_TOKEN")
    if not token:raise SystemExit("AB21_SOURCE_TOKEN missing: no files changed")
    updates=[]
    for pair in PAIRS:
        rows,last=validate(pair,fetch(pair,token))
        dest=ROOT/"research_data"/"fx_sessions"/"H1"/f"{pair}.csv"
        if dest.exists():
            with dest.open(encoding="utf-8-sig",newline="") as f:old=list(csv.DictReader(f))
            if old:
                old_end=datetime.fromisoformat(old[-1]["EndUTC"].replace("Z","+00:00"))
                if last<old_end:raise ValueError(f"{pair}: source older than public; refusing rollback")
        out=io.StringIO()
        writer=csv.DictWriter(out,fieldnames=FIELDS,lineterminator="\n")
        writer.writeheader();writer.writerows({k:r[k] for k in FIELDS} for r in rows)
        updates.append((dest,out.getvalue()))
    # All-or-nothing validation: write only after all 21 pass.
    for dest,content in updates:
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(content,encoding="utf-8")
    print("Validated and staged 21 sanitized research-only CSVs; source branch",REF)
if __name__=="__main__":main()
