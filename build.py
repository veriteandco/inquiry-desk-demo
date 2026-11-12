"""Build the Inquiry Desk demo.

Generates fully synthetic sample inquiries (made-up names, venues and towns,
random dates and guest counts) from a fixed seed, drops them into src/desk.html
and writes one self-contained file: inquiry-desk.html.

    python3 -I build.py

No real data is read. Change SEED to get a different set of samples.
"""
import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = 7
TODAY = date(2026, 11, 10)
N = 320

FIRST = ["Avery", "Jordan", "Maya", "Liam", "Nora", "Eli", "Claire", "Owen", "Hazel", "Theo",
         "Ruby", "Miles", "Iris", "Jonah", "Stella", "Felix", "June", "Caleb", "Lena", "Rhys",
         "Willa", "Dean", "Paige", "Silas", "Tessa", "Gabe", "Elise", "Reid", "Mara", "Wes",
         "Quinn", "Ada", "Cole", "Ivy", "Luca", "Daphne", "Noah", "Greta", "Asher", "Celia"]
LAST = "ABCDEFGHJKLMNPRSTVWY"
# Fictional venues and towns. Any resemblance to real places is coincidence.
VENUES = ["Alder Hollow Barn", "Fernbrook Estate", "Larkspur Hall", "Stonebridge Farm",
          "Marlow Pond Lodge", "Wren Meadow", "Copper Kettle Mill", "Birchwood Pavilion"]
TOWNS = ["Pinecrest Falls", "Marlow Springs", "Eastvale", "Oakhaven", "River Bend",
         "Thistle Creek", "Harlow Point", "Linden Mills"]

TYPES = [("Wedding", 62), ("Not said", 8), ("Party", 7), ("Birthday", 5), ("Corporate", 5),
         ("Shower", 4), ("Engagement", 3), ("Rehearsal", 3), ("Graduation", 3)]
ASKS = [("price", "Asked for pricing and packages.", .45), ("trailer", "Interested in the trailer.", .25),
        ("signature", "Wants signature cocktails.", .2), ("beerwine", "Asked about a beer and wine only bar.", .08),
        ("mocktail", "Asked about non-alcoholic drinks.", .06), ("coffee", "Asked about coffee and espresso.", .05),
        ("license", "Asked about the liquor license.", .06), ("openbar", "Asked about an open bar.", .08),
        ("indoor", "Event is indoors or under a tent.", .08), ("referral", "Was referred by someone.", .12),
        ("chaser", "Wrote again because they hadn't heard back.", .06), ("availability", "Asked if the date is open.", .3)]
YEAR_WEIGHT = {2023: 40, 2024: 70, 2025: 90, 2026: 120}
MONTH_WRITE = [12, 12, 14, 12, 10, 8, 6, 4, 3, 5, 4, 3]            # when people write
MONTH_EVENT = [1, 1, 2, 3, 8, 9, 8, 9, 28, 26, 4, 2]                # when events happen


def wchoice(r, pairs):
    return r.choices([p[0] for p in pairs], [p[1] for p in pairs])[0]


def make():
    r = random.Random(SEED)
    start = date(2023, 5, 1)
    days = [start + timedelta(d) for d in range((TODAY - start).days + 1)]
    wts = []
    for d in days:
        wts.append(YEAR_WEIGHT[d.year] / 365 * MONTH_WRITE[d.month - 1] * (4 if (TODAY - d).days <= 10 else 1))
    created_days = sorted(r.choices(days, wts, k=N))
    out = []
    people = []
    for i, cd in enumerate(created_days):
        etype = wchoice(r, TYPES)
        if people and r.random() < .06:
            person, name = r.choice(people)
        else:
            name = f"{r.choice(FIRST)} {r.choice(LAST)}."
            person = f"p{i}"
            people.append((person, name))
        created = datetime(cd.year, cd.month, cd.day, r.randint(7, 22), r.choice([0, 12, 26, 41, 55]))
        ev, prec = None, None
        if r.random() < .85:
            lo, hi = cd + timedelta(20), cd + timedelta(600)
            cand = [lo + timedelta(k) for k in range((hi - lo).days)]
            w = [MONTH_EVENT[c.month - 1] * (6 if c.weekday() == 5 else 1) for c in cand]
            ev = r.choices(cand, w)[0]
            prec = "day"
            if r.random() < .12:
                ev, prec = ev.replace(day=15), "month"
        guests = None
        if r.random() < .88:
            guests = int(min(260, max(25, r.lognormvariate(4.7, .45))))
        flags = [f for f, _, p in ASKS if r.random() < p]
        loc, known = "", False
        x = r.random()
        if x < .35:
            loc, known = r.choice(VENUES), True
        elif x < .65:
            loc = "Private home, " + r.choice(TOWNS)
        elif x < .85:
            loc = r.choice(TOWNS)
        channel = "Chat" if r.random() < .3 else "Form"
        bits = []
        if etype != "Not said":
            bits.append(f"{etype}" + (f" for about {guests} guests" if guests else "") + (f" at {loc}" if known else "") + ".")
        bits += [s for f, s, _ in ASKS if f in flags]
        if channel == "Chat" and not bits:
            bits.append("Sent a question through the website chat.")
        out.append({
            "id": i + 1, "person": person, "name": name,
            "created": created.strftime("%Y-%m-%dT%H:%M"), "channel": channel,
            "device": "Mobile" if r.random() < .6 else "Desktop",
            "guestsText": str(guests) if guests else "", "guests": guests,
            "location": loc, "knownVenue": known,
            "eventDate": ev.isoformat() if ev else None, "datePrecision": prec,
            "eventDateText": "", "type": etype, "flags": flags,
            "message": " ".join(bits) or "Filled out the form without a message.",
            "timesWritten": 2 if any(p == person for p, _ in people[:-1]) and r.random() < .5 else 1,
        })
    return out


def main():
    rows = make()
    data = {"today": TODAY.isoformat(), "source": "Randomly generated sample data", "inquiries": rows}
    tpl = (HERE / "src" / "desk.html").read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = tpl.replace("/*__DATA__*/null", payload)
    (HERE / "inquiry-desk.html").write_text(html, encoding="utf-8")
    print(f"{len(rows)} sample inquiries, {len(html)//1024} KB written")


if __name__ == "__main__":
    main()
