#!/usr/bin/env python3
"""Audit 21 published research CSVs without fabricating fresh prices."""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAIRS="USDJPY EURJPY GBPJPY AUDJPY NZDJPY CADJPY CHFJPY EURUSD GBPUSD AUDUSD NZDUSD USDCAD USDCHF EURGBP EURAUD EURNZD EURCHF GBPAUD GBPCHF AUDNZD AUDCHF".split()
def main():
    now=datetime.now(timezone.utc)
    rows=[]
    for pair in PAIRS:
        path=ROOT/"research_data"/"fx_sessions"/"H1"/(pair+".csv")
        if not path.exists():
            rows.append({"pair":pair,"status":"MISSING"});continue
        with path.open(encoding="utf-8-sig",newline="") as f:
            data=list(csv.DictReader(f))
        if not data:
            rows.append({"pair":pair,"status":"EMPTY"});continue
        try:
            times=[datetime.fromisoformat(r["EndUTC"].replace("Z","+00:00")) for r in data]
            good=all(r["Pair"]==pair and r["Status"]=="PROVISIONAL_NOT_TRADEABLE" for r in data)
            ordered=all(a<b for a,b in zip(times,times[1:]))
            age=round((now-times[-1]).total_seconds()/3600,1)
            status="OK" if good and ordered and 0<=age<=4 else "STALE" if good and ordered and age>4 else "INVALID"
            rows.append({"pair":pair,"status":status,"latest_utc":times[-1].isoformat(),"age_hours":age,"bars":len(data)})
        except (KeyError,ValueError,TypeError):
            rows.append({"pair":pair,"status":"INVALID"})
    output={"mode":"RESEARCH_ONLY","checked_at_utc":now.isoformat(),"total":len(PAIRS),"healthy":sum(r["status"]=="OK" for r in rows),"pairs":rows}
    dest=ROOT/"data_quality"/"price_feed_status.json"
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Price CSV audit: {output['healthy']}/{len(PAIRS)} healthy. No price updates performed.")
if __name__=="__main__":main()
