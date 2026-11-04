#!/usr/bin/env python3
"""Build the brief pool: briefs/e1.jsonl (200), e2_train.jsonl (500), e2_eval.jsonl (100, HELD OUT).
Seeded, data-independent. Splits are disjoint by construction and verified (exact + normalized text).
  .venv/bin/python scripts/make_briefs.py            # write
  .venv/bin/python scripts/make_briefs.py --check    # only verify the committed files
"""
import argparse, json, random, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "briefs"
SPLITS = [("e1", 200), ("e2_train", 500), ("e2_eval", 100)]

INDUSTRIES = {
    "fintech": ["a budgeting app for freelancers", "an invoice-factoring service", "a spare-change investing app", "a business expense card", "a tax-prep assistant", "a cross-border payments tool", "a bill-splitting app", "a credit-score coach"],
    "health": ["a telehealth clinic for sleep problems", "a physical-therapy exercise app", "a mental-health journaling app", "a genetic-testing kit", "a pediatric urgent-care chain", "a medication reminder service", "a hearing-aid retailer", "a postpartum care program"],
    "food": ["a meal-kit delivery service", "an artisan coffee roaster", "a plant-based butcher", "a hot-sauce subscription", "a neighborhood bakery", "a farm-box CSA", "a craft-soda brand", "a ghost-kitchen platform"],
    "education": ["an online coding bootcamp", "a language-learning app", "a tutoring marketplace", "a K-12 math game", "a nursing exam prep course", "a music-theory course", "a university admissions consultancy", "a community pottery school"],
    "travel": ["a boutique hostel network", "a van-rental service", "a guided hiking-tour company", "a travel-insurance comparison site", "a luxury train journey", "an eco-lodge in Costa Rica", "a city walking-tour app", "a pet-friendly hotel finder"],
    "saas": ["a customer-support helpdesk", "a project-management tool for agencies", "an API monitoring service", "a no-code form builder", "a developer documentation platform", "a employee-onboarding tool", "a product-analytics dashboard", "a password manager for teams"],
    "real estate": ["a co-living operator", "a home-staging studio", "a property-management platform", "a mortgage broker", "a commercial-office marketplace", "a vacation-rental management firm", "a tiny-home builder", "a landlord insurance product"],
    "fitness": ["a boutique climbing gym", "a home-rowing machine", "a yoga studio chain", "a personal-training marketplace", "a running-shoe brand", "a recovery and cold-plunge spa", "a kids' martial-arts academy", "a cycling-club app"],
    "fashion": ["a sustainable denim label", "a rental wardrobe service", "a custom-suit tailor", "a vintage-sneaker reseller", "a handmade jewelry shop", "a modest-wear boutique", "an outdoor-gear brand", "a eyewear direct-to-consumer brand"],
    "nonprofit": ["a river-cleanup charity", "a food-bank network", "a rural library fund", "an animal-rescue shelter", "a refugee legal-aid group", "a youth-mentoring program", "a reforestation initiative", "a disaster-relief fund"],
    "creative": ["a wedding photography studio", "a podcast production agency", "a freelance illustrator portfolio", "an indie game studio", "a boutique branding agency", "a stock-music library", "a film-festival", "a letterpress print shop"],
    "home": ["a solar-panel installer", "a smart-thermostat maker", "a custom-cabinet workshop", "a houseplant delivery service", "a residential cleaning company", "a mattress brand", "a home-energy audit service", "a handyman booking app"],
    "legal": ["an immigration law firm", "a startup incorporation service", "an estate-planning platform", "a contract-review tool", "a patent-filing boutique", "a tenant-rights clinic", "a trademark search tool", "a mediation practice"],
    "auto": ["an electric-scooter brand", "a mobile car-detailing service", "a EV-charging network", "a classic-car restoration shop", "a driving-school app", "a used-car inspection service", "a motorcycle-gear retailer", "a fleet-telematics product"],
    "events": ["a conference-ticketing platform", "a micro-festival for makers", "a corporate-retreat planner", "a wedding-venue marketplace", "a live-trivia night company", "a virtual-event studio", "a food-truck rally", "a charity gala organizer"],
    "pets": ["a raw-food dog brand", "a pet-sitting marketplace", "a veterinary telemedicine app", "a cat-furniture studio", "a dog-training academy", "an aquarium supply store", "a pet-insurance provider", "a horse-boarding stable"],
    "science and hardware": ["a desktop 3D-printer maker", "a maker-space membership", "a satellite-imagery API", "a lab-equipment marketplace", "a home weather-station kit", "a robotics kit for schools", "a quantum-computing cloud", "a open-source microscope"],
    "media": ["a niche newsletter network", "an independent bookstore", "a local news cooperative", "a audiobook subscription", "a documentary streaming service", "a comic-book publisher", "a vinyl-record club", "a magazine for woodworkers"],
    "local services": ["a family dental practice", "a neighborhood bike shop", "a barbershop", "a plumbing company", "a wedding florist", "a tutoring center", "a moving company", "a dry cleaner with pickup"],
    "b2b": ["a freight-matching marketplace", "a warehouse-robotics vendor", "a recruiting agency for nurses", "a HR payroll provider", "a cybersecurity consultancy", "a industrial-sensor maker", "a B2B packaging supplier", "a commercial-kitchen equipment dealer"],
}
QUALIFIERS = ["", "that launched this year", "with a strong local focus", "known for fast support", "priced for small budgets", "aimed at the premium end", "run by a two-person team", "with a mission-first story", "that just raised a seed round", "with 20 years of history"]
AUDIENCES = ["busy parents", "college students", "small-business owners", "retirees", "software engineers", "first-time home buyers", "creative freelancers", "enterprise IT buyers", "outdoor enthusiasts", "health-conscious professionals", "local families", "startup founders", "teachers", "gamers", "luxury shoppers", "budget-conscious shoppers", "nonprofit program managers", "recent graduates", "athletes", "remote workers", "city commuters", "hobbyists and makers", "healthcare administrators", "wedding planners"]
TONES = ["playful and bright", "calm and trustworthy", "bold and high-energy", "minimal and editorial", "warm and friendly", "luxurious and refined", "technical and precise", "earthy and handmade", "futuristic and sleek", "no-nonsense and direct", "quirky and irreverent", "optimistic and mission-driven", "dark and moody", "retro and nostalgic", "clean and clinical"]
SECTIONS = ["features", "pricing", "testimonials", "FAQ", "how it works", "team", "gallery", "logo wall", "stats", "contact form", "newsletter signup", "case studies", "comparison table", "blog preview", "locations", "integrations", "app download"]
SYL = ["lum", "nor", "vel", "tri", "ka", "bo", "mer", "sol", "pix", "ora", "zen", "dra", "fi", "lo", "ba", "ten", "qui", "ar", "mo", "sy", "ve", "ni", "co", "ra", "el", "um", "ta", "gi"]


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def name(rng):
    return "".join(rng.choice(SYL) for _ in range(rng.choice([2, 3]))).capitalize()


def make_one(rng, industry, product):
    q = rng.choice(QUALIFIERS)
    aud, tone = rng.choice(AUDIENCES), rng.choice(TONES)
    secs = ["hero"] + rng.sample(SECTIONS, rng.randint(3, 5))
    if rng.random() < 0.8: secs.insert(rng.randint(2, len(secs)), "CTA")
    secs.append("footer")
    nm = name(rng)
    biz = f"{nm}, {product}" + (f" {q}" if q else "")
    desc = f"Landing page for {biz}, for {aud}; tone: {tone}."
    return {"product": biz, "industry": industry, "audience": aud, "tone": tone, "sections": secs, "description": desc}


def build(seed=20261103):
    rng = random.Random(seed)
    prods = [(i, p) for i, ps in INDUSTRIES.items() for p in ps]
    need = sum(n for _, n in SPLITS)
    # every (industry, product) used at most ceil(need/len) times, shuffled so splits are mixed
    pool = []
    reps = -(-need // len(prods))
    for _ in range(reps): pool += prods
    rng.shuffle(pool)
    seen, rows = set(), []
    for ind, prod in pool:
        if len(rows) == need: break
        for _ in range(50):
            b = make_one(rng, ind, prod)
            keys = {norm(b["description"]), norm(b["product"])}
            if not keys & seen: seen |= keys; rows.append(b); break
    assert len(rows) == need, len(rows)
    out, k = {}, 0
    for s, n in SPLITS:
        out[s] = []
        for b in rows[k:k + n]:
            out[s].append({"id": f"{s}-{len(out[s]):04d}", **b})
        k += n
    return out


def check():
    allrows, texts = [], {}
    for s, n in SPLITS:
        rows = [json.loads(l) for l in (OUT / f"{s}.jsonl").read_text().splitlines()]
        assert len(rows) == n, f"{s}: {len(rows)} != {n}"
        texts[s] = rows; allrows += rows
    ids = [r["id"] for r in allrows]; assert len(set(ids)) == len(ids), "duplicate ids"
    for field in ("description", "product"):
        ex = [r[field] for r in allrows]; assert len(set(ex)) == len(ex), f"exact duplicate {field}"
        nm = [norm(x) for x in ex]; assert len(set(nm)) == len(nm), f"normalized duplicate {field}"
    for r in allrows:
        assert all(r.get(k) for k in ("id", "product", "audience", "tone", "sections", "description"))
    print(f"OK: {[(s, len(texts[s])) for s in texts]} disjoint (exact + normalized) across all splits")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--check", action="store_true"); ap.add_argument("--seed", type=int, default=20261103)
    a = ap.parse_args()
    if not a.check:
        OUT.mkdir(exist_ok=True)
        for s, rows in build(a.seed).items():
            (OUT / f"{s}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        (OUT / "command.txt").write_text(" ".join([sys.executable] + sys.argv) + f"\nseed={a.seed}\n")
    check()
