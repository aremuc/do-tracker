import hashlib
import html
import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def canonical(url):
    p = urlsplit(html.unescape(clean(url)))
    if p.scheme not in ("http", "https") or not p.hostname:
        return ""
    keep = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
            if not k.lower().startswith("utm_") and k.lower() not in
            {"ref", "source", "sourceid", "gh_src", "lever-source", "lever-origin", "embed"}]
    path = p.path.rstrip("/")
    if "ashbyhq.com" in p.netloc or "lever.co" in p.netloc:
        path = re.sub(r"/application$", "", path)
    return urlunsplit(("https", p.netloc.lower(), path, urlencode(sorted(keep)), ""))


def identity(url):
    u = canonical(url)
    p = urlsplit(u)
    # Stable IDs remove language / display-title / application-path differences.
    for host, pattern in [("lever.co", r"/([^/]+)/([a-f0-9-]{36})"),
                          ("ashbyhq.com", r"/([^/]+)/([a-f0-9-]{36})"),
                          ("myworkdayjobs.com", r"_([A-Za-z0-9-]+)$")]:
        m = re.search(pattern, p.path)
        if host in p.netloc and m:
            return p.netloc + ":" + ":".join(m.groups())
    return u


def date_string(value):
    if not value:
        return None
    try:
        if isinstance(value, (float, int)):
            return datetime.fromtimestamp(value / 1000, timezone.utc).date().isoformat()
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date().isoformat()
    except (ValueError, TypeError, OverflowError):
        return None


def category(title, config):
    t = title.lower()
    # A support role reporting to a director/chief is not that senior role.
    primary_title = re.split(r"\s+to\s+(?:the\s+)?", t, maxsplit=1)[0]
    if any(re.search(p, primary_title) for p in config["exclude_title_patterns"]):
        return None
    for name, terms in config["categories"].items():
        if any(term in t for term in terms):
            return name
    return None


def french_signal(title, text):
    """Do not mistake explicitly other-language roles for French opportunities."""
    explicit_french = bool(re.search(r"french|français|francais|\bfr[/ -]en\b|\ben[/ -]fr\b", title, re.I))
    other_language = bool(re.search(r"mandarin|cantonese|spanish|arabic|portuguese|korean|japanese|german|italian", title, re.I))
    if other_language and not explicit_french:
        return False
    return explicit_french or bool(re.search(r"\b(?:bilingual|french|français|francais)\b", title + " " + text, re.I))


def assess(raw, config):
    title = clean(raw.get("title"))
    cat = category(title, config)
    if not cat:
        return None
    if cat == "Client services" and re.search(r"\b(?:rbc|td bank|royal bank|cibc|bmo|scotiabank|national bank|banque)\b", clean(raw.get("company")), re.I):
        cat = "Banking and insurance fallback"
    text = clean(raw.get("description"))
    lower = (title + " " + text).lower()
    loc = clean(raw.get("location"))
    city = next((c for c in config["preferred_cities"] + config["commute_review_cities"]
                 if re.search(r"\b" + re.escape(c) + r"\b", loc, re.I)), None)
    remote = raw.get("is_remote") is True or bool(re.search(r"\bremote\b", title, re.I))
    if re.search(r"\b(?:united states|usa|united kingdom)\b", loc, re.I):
        return None
    if not city and not (remote and re.search(r"\b(?:canada|ontario)\b", loc, re.I)):
        return None
    if re.search(r"internal applicants only|current employees only", lower):
        return None
    flags = ["Confirm experience, software skills and language requirements before applying"]
    if city != "toronto" and city:
        flags.append("Commute review: transit time to this location has not been checked")
    if remote:
        flags.append("Confirm Ontario eligibility, office visits and remote-work restrictions")
    bilingual = french_signal(title, text)
    if bilingual:
        flags.append("French/bilingual signal: confirm spoken and written proficiency requirements")
    if re.search(r"licen[cs]e|certification|mutual funds|csc|ific", lower):
        flags.append("Check required licences/certifications and whether training is provided")
    if re.search(r"driver.?s licen[cs]e|personal vehicle|own vehicle", lower):
        flags.append("Check driving requirements")
    experienced = bool(re.search(r"\b(?:[4-9]|1[0-9])\+?\s*(?:years|year)[’'s]*\s*(?:of )?(?:relevant )?experience", lower))
    if experienced or re.search(r"\b(?:senior|supervisor|manager)\b", title, re.I):
        flags.append("Review experience/supervisory requirements carefully")
    contract = bool(re.search(r"\b(?:casual|temporary|fixed.term|part.time|contract (?:role|position)|\d+[- ]month contract)\b", lower) or re.search(r"contract|temporary|parttime|casual", clean(raw.get("job_type")), re.I))
    fulltime = bool(re.search(r"permanent|full.time|fulltime|budget - continuing", lower + " " + clean(raw.get("job_type"))))
    employment = "Temporary / contract / part-time — review" if contract else ("Full-time/permanent advertised — confirm terms" if fulltime else "Not established")
    if re.search(r"(?:no|without|not eligible for)\s+(?:extended health |health |medical |employee |group )?benefits|benefits\s+(?:are )?not (?:offered|provided|available)|(?:do(?:es)? not|don.t|doesn.t) (?:offer|provide|include)[^.!\n]{0,30}(?:health|medical|dental)[^.!\n]{0,20}(?:insurance|benefits|coverage)", lower):
        benefits = "Not offered in text"
    elif re.search(r"health (?:and dental|insurance|benefits|coverage)|medical (?:and dental|insurance|benefits|coverage)|dental (?:insurance|benefits|coverage)|extended health|group benefits|comprehensive benefits|employee benefits package", lower):
        benefits = "Advertised — confirm coverage"
    else:
        benefits = "Not stated / not extracted"
    if benefits.startswith("Advertised"):
        flags.append("Confirm benefit eligibility, coverage, employee contributions and waiting period")
    else:
        flags.append("Health/dental benefits require confirmation")
    waiting = bool(re.search(r"waiting period|after (?:\d+|three|six|3|6) months|following probation", lower))
    if waiting:
        flags.append("Eligibility/probation period mentioned: check when benefits begin")
    # Detect explicit arrangements; generic remote words inside company boilerplate are insufficient.
    if re.search(r"\bhybrid\b", lower) and not re.search(r"not (?:a )?hybrid|no hybrid|hybrid[^.!\n]{0,20}not available", lower):
        workplace = "Hybrid advertised"
    elif re.search(r"(?:work (?:location|setting|arrangement|mode)|workplace|position|role)[: -]+(?:in.person|on.site)|\bon.site\b|\bin.person\b", lower):
        workplace = "In-person advertised"
    elif remote or re.search(r"fully remote|100% remote|work from home|remote (?:role|position|work arrangement)", lower):
        workplace = "Remote advertised"
    else:
        workplace = "Not stated / not extracted"
    weekday = bool(re.search(r"monday\s*(?:to|through|[-–])\s*friday|mon\s*[-–]\s*fri|no weekends", lower))
    # Remove explicit negations before flagging weekend requirements.
    weekend_text = re.sub(r"no weekends?(?: required)?|weekends? (?:are )?not required|excluding weekends?", "", lower)
    weekend = bool(re.search(r"saturdays?|sundays?|weekends?", weekend_text))
    evenings = bool(re.search(r"evening|rotating shifts?|night shifts?|24/7|24.hour|overtime", lower))
    schedule = "Weekday pattern + extra-hours signal — review" if weekday and (weekend or evenings) else ("Weekdays advertised" if weekday else ("Weekend/shift signal — review" if weekend or evenings else "Not stated / not extracted"))
    if weekend or evenings:
        flags.append("Check mandatory versus optional weekends, evenings, shifts and overtime")
    if re.search(r"(?:no|not (?:provide|offer|available)|without)[^.!\n]{0,55}(?:visa|immigration|work permit) sponsorship|(?:visa|immigration|work permit) sponsorship[^.!\n]{0,35}(?:not available|not offered|not provided|unavailable)", lower):
        support = "Not offered in text"
    elif re.search(r"(?:visa|immigration|work permit) (?:sponsorship|support|assistance)[^.!\n]{0,40}(?:available|provided|offered)|(?:provide|offer)[^.!\n]{0,35}(?:visa|immigration|work permit) (?:sponsorship|support|assistance)", lower):
        support = "Advertised — confirm with employer"
    else:
        support = "Not stated / not extracted"
    salary = raw.get("salary") or "Not disclosed / not extracted"
    annual = None
    low, high, interval = raw.get("min_amount"), raw.get("max_amount"), raw.get("interval")
    currency = raw.get("currency") or "CAD"
    if isinstance(low, (int, float)) and low > 0:
        if interval == "yearly" and low < 10000:
            flags.append("Salary unit inconsistent: verify the posting")
        else:
            salary = f"{currency} {low:,.2f}" + (f"–{high:,.2f}" if high and high != low else "") + f" / {interval or 'period unknown'}"
            if interval == "yearly" and currency == "CAD":
                annual = low
    # Use an explicit annual salary range when the board omits structured fields.
    if annual is None:
        match = re.search(r"\$\s*(\d{2,3}[, ]\d{3})(?:\.\d{2})?\s*(?:[-–]|to)\s*\$?\s*(\d{2,3}[, ]\d{3})(?:\.\d{2})?\s*(?:a |per |/)?(?:year|annum|annually)", lower)
        if match:
            if re.search(r"\bcad\b|canadian dollars|c\$", lower):
                annual = float(re.sub(r"[, ]", "", match[1]))
            salary = f"Advertised annual range: ${match[1]}–${match[2]} (confirm currency)"
            flags.append("Annual range extracted from text; confirm currency and base versus total compensation")
    commission = bool(re.search(r"commission.only|100% commission|commission.based", lower))
    if commission:
        flags.append("Confirm guaranteed base pay; commission cannot be assumed")
    fallback = contract or commission or cat == "Banking and insurance fallback" or benefits == "Not offered in text" or (annual is not None and annual < config["salary_review_floor"])
    strong = fulltime and benefits.startswith("Advertised") and workplace in ("Hybrid advertised", "In-person advertised") and not weekend and not evenings and not experienced and (annual is None or annual >= config["salary_target"])
    tier = "Fallback" if fallback else ("Priority" if strong else "Review")
    score = (3 if benefits.startswith("Advertised") else 0) + (3 if workplace == "Hybrid advertised" else 2 if workplace == "In-person advertised" else 0) + (2 if weekday and not weekend and not evenings else 0) + int(fulltime and not contract) + int(bilingual) + int(annual is not None and annual >= config["salary_target"])
    if annual is None:
        flags.append("Annual base pay unknown; hourly rates are not annualized without confirmed hours")
    sentences = re.split(r"\n+|(?<=[.!?])\s+", text)
    relevant = [s.strip(" *#\t") for s in sentences if re.search(r"benefit|dental|health|salary|\$|hybrid|monday|weekend|sponsor|experience|full.time", s, re.I)]
    evidence = " ".join(" ".join(relevant[:6]).split()[:90])
    return {"category": cat, "tier": tier, "employment": employment, "flags": flags, "salary": salary,
            "evidence": evidence, "benefits": benefits, "workplace": workplace, "schedule": schedule,
            "employer_support": support, "bilingual_signal": bilingual, "preference_score": score,
            "annual_base_min": annual, "match_reason": f"Title matches {cat.lower()}; advertised preferences are signals, not a qualification assessment"}


def merge(existing, incoming, config, now):
    records = {j["id"]: dict(j) for j in existing}
    aliases = {identity(u): j["id"] for j in existing for u in j.get("urls", []) if identity(u)}
    for raw in incoming:
        assessment = assess(raw, config)
        if not assessment:
            continue
        urls = [canonical(raw.get(k, "")) for k in ("job_url_direct", "job_url")]
        urls = [u for u in urls if u]
        if not urls:
            continue
        found = {aliases[identity(u)] for u in urls if identity(u) in aliases}
        jid = sorted(found)[0] if found else hashlib.sha256(identity(urls[0]).encode()).hexdigest()[:16]
        old = records.get(jid, {})
        # If a newly discovered direct URL bridges two older records, unite them.
        for other in found - {jid}:
            duplicate = records.pop(other)
            old["urls"] = sorted(set(old.get("urls", []) + duplicate.get("urls", [])))
            old["first_seen"] = min(old.get("first_seen", now), duplicate.get("first_seen", now))
            old["sources"] = sorted(set(old.get("sources", []) + duplicate.get("sources", [])))
        urls = sorted(set(urls + old.get("urls", [])))
        previous_url = old.get("url")
        job = {**old, **assessment, "id": jid, "title": clean(raw.get("title")),
               "company": clean(raw.get("company")), "location": clean(raw.get("location")),
               "url": canonical(raw.get("job_url_direct")) or old.get("url") or canonical(raw["job_url"]),
               "urls": urls, "posted_date": date_string(raw.get("date_posted")) or old.get("posted_date"),
               "posted_date_basis": raw.get("date_basis", "Source-reported; may be board-added date"),
               "first_seen": old.get("first_seen", now), "last_seen": now,
               "sources": sorted(set(old.get("sources", []) + [clean(raw.get("site")) or "manual"])),
               "status": old.get("status", "Unverified")}
        if previous_url and job["url"] != previous_url:
            job["status"] = "Unverified"
            for field in ("last_checked", "last_verified", "deadline", "missing_since"):
                job.pop(field, None)
            job["verification_note"] = "Application URL changed; new destination needs checking"
        records[jid] = job
        for u in urls:
            aliases[identity(u)] = jid
    for job in records.values():
        if job.get("status") != "Closed" and datetime.fromisoformat(job["last_seen"]) < datetime.fromisoformat(now) - timedelta(days=config["stale_after_days"]):
            job["status"] = "Stale — recheck"
    return list(records.values())


def atomic_json(path, obj):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


PUBLIC_JOB_FIELDS = frozenset({
    "category", "company", "deadline", "employment", "evidence", "first_seen",
    "flags", "id", "last_checked", "last_seen", "last_verified", "location",
    "match_reason", "posted_date", "posted_date_basis", "salary", "sources",
    "status", "tier", "title", "url", "urls", "verification_note",
    "benefits", "workplace", "schedule", "employer_support", "bilingual_signal", "preference_score", "annual_base_min",
    "missing_since", "employer_posted_date", "exclusion_reason", "status_before_exclusion",
})


def public_jobs(jobs):
    """Export only listing metadata; never carry private tracking fields forward."""
    return [{key: value for key, value in job.items() if key in PUBLIC_JOB_FIELDS}
            for job in jobs]


def apply_scope(jobs, config, now):
    """Reapply title exclusions to stored listings without deleting their history."""
    for job in jobs:
        if job.get("bilingual_signal") and re.search(r"mandarin|cantonese|spanish|arabic|portuguese|korean|japanese|german|italian", job["title"], re.I) and not french_signal(job["title"], ""):
            job["bilingual_signal"] = False
            job["preference_score"] = max(0, job.get("preference_score", 0) - 1)
            job["flags"] = [f for f in job.get("flags", []) if not f.startswith("French/bilingual signal")]
        if category(job["title"], config) is None:
            if job["status"] != "Excluded":
                job["status_before_exclusion"] = job["status"]
            job["status"] = "Excluded"
            job["exclusion_reason"] = "Outside configured job families or excluded role"
            continue
        if job["status"] == "Excluded":
            job["status"] = job.pop("status_before_exclusion", "Unverified")
            job.pop("exclusion_reason", None)
        deadline = date_string(job.get("deadline"))
        if deadline and deadline < now[:10]:
            job["status"] = "Closed"
            job["verification_note"] = "Previously observed employer deadline has passed"
        elif job["status"] != "Closed" and datetime.fromisoformat(job["last_seen"]) < datetime.fromisoformat(now) - timedelta(days=config["stale_after_days"]):
            job["status"] = "Stale — recheck"
    return jobs
