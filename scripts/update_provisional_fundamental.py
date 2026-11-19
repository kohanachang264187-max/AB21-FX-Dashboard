#!/usr/bin/env python3
"""Public, free ECB reference-rate provisional FX momentum; not macro fundamentals."""
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

URL="https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml"
CCY=("USD","EUR","JPY","GBP","CHF","AUD","NZD","CAD")
PAIRS=("USDJPY EURJPY GBPJPY AUDJPY NZDJPY CADJPY CHFJPY EURUSD GBPUSD AUDUSD NZDUSD USDCAD USDCHF EURGBP EURAUD EURNZD EURCHF GBPAUD GBPCHF AUDNZD AUDCHF").split()
OUT=Path(__file__).resolve().parents[1]/"fundamental_output"/"fundamental_latest.json"

def main():
    request=urllib.request.Request(URL,headers={"User-Agent":"AB21-Research-Only/1.0"})
    with urllib.request.urlopen(request,timeout=30) as response:
        root=ET.fromstring(response.read())
    days={}
    for node in root.iter():
        day=node.attrib.get("time")
        if not day:continue
        rates={"EUR":1.0}
        for child in node:
            currency=child.attrib.get("currency")
            if currency in CCY:
                rates[currency]=float(child.attrib["rate"])
        if all(c in rates for c in CCY):
            days[day]=rates
    dates=sorted(days)
    if len(dates)<6:raise RuntimeError("ECB history insufficient")
    end,start=dates[-1],dates[-6]
    latest,prior=days[end],days[start]
    # 5-observation change against EUR. Center across all eight currencies.
    change={c:100*(latest[c]/prior[c]-1) for c in CCY}
    center=sum(change.values())/len(CCY)
    values={c:change[c]-center for c in CCY}
    max_abs=max(abs(v) for v in values.values())
    if max_abs<=0:raise RuntimeError("All currencies unchanged; cannot rank")
    score={c:round(5*values[c]/max_abs,3) for c in CCY}
    currencies={c:{"status":"PROVISIONAL","score":score[c],"missing_factors":["policy_rate","inflation","growth","yield","positioning"],"method":"ECB_5_OBSERVATION_FX_MOMENTUM_PROXY_NOT_FUNDAMENTAL"} for c in CCY}
    pairs=[]
    for p in PAIRS:
        value=round(score[p[:3]]-score[p[3:]],3)
        pairs.append({"pair":p,"score_difference":value,"status":"PROVISIONAL","method":"FX_MOMENTUM_PROXY"})
    pairs.sort(key=lambda x:x["score_difference"],reverse=True)
    for i,p in enumerate(pairs,1):p["rank"]=i
    result={"schema_version":"1.0","mode":"RESEARCH_ONLY","generated_at_utc":datetime.now(timezone.utc).isoformat(),"ranked_count":0,"provisional_count":len(pairs),"provisional_method":"ECB five-observation FX reference-rate momentum; NOT macro fundamentals; missing all five macro factors","source_observation_start":start,"source_observation_end":end,"currencies":currencies,"pairs":pairs,"sources":{"ECB_FX_REFERENCE_RATES":{"observations":[{"date":end,"value":"ECB reference rates for 7 currencies against EUR"}],"audit":{"ok":True},"url":URL}}}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Wrote provisional FX proxy",end,len(pairs))
if __name__=="__main__":main()
