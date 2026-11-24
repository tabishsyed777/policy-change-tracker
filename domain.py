"""Policy Change Tracker domain retrieval and answer rules."""
NAME = '08-policy-change-tracker'

import re
from datetime import date
from common import norm,require
FIELDS=("topic","effective","rule")
DATE=r"[0-9]{4}-[0-9]{2}-[0-9]{2}"

def validate(rows):
    seen=set()
    for r in rows:
        require(re.fullmatch(DATE,r["effective"]),"use ISO effective date")
        date.fromisoformat(r["effective"])
        key=norm(r["topic"]),r["effective"]
        require(key not in seen,"ambiguous effective date")
        seen.add(key)

def solve(rows,q):
    q=q.rstrip("?")
    diff=re.fullmatch(fr"changes to (.+?) from ({DATE}) to ({DATE})",q)
    m=diff or re.fullmatch(fr"(.+?) on ({DATE})",q)
    if not m: return
    topic,*days=m.groups()
    try: parsed=[date.fromisoformat(d) for d in days]
    except ValueError: return
    if parsed!=sorted(parsed): return
    ev=[]
    for day in days:
        valid=[r for r in rows if norm(r["topic"])==topic and r["effective"]<=day]
        if not valid: return
        ev.append(max(valid,key=lambda r:r["effective"]))
    if not diff: return ev[0]["rule"],ev,"effective date"
    first,last=ev
    if first["rule"]==last["rule"]:
        return "Unchanged: "+first["rule"],([first] if first==last else ev),"endpoint comparison"
    return first["rule"]+" → "+last["rule"],ev,"endpoint comparison"
