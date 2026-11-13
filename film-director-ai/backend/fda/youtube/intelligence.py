"""YouTube Intelligence: public research through the YouTube Data API, the owner's authorised analytics through OAuth +
YouTube Analytics API, dated snapshots, and an analysis engine that keeps correlation and causation apart."""
import re
import statistics
import time
import urllib.parse
from datetime import date, datetime, timedelta, timezone

from itsdangerous import BadSignature, URLSafeTimedSerializer

from fda.auth.security import decrypt, encrypt
from fda.config import get_settings
from fda.database import models as m
from fda.knowledge.ingestion import ingest
from fda.providers import registry
from fda.providers.base import NotConfigured, ProviderError, http
from fda.services.llm import LLM, external

API = "https://www.googleapis.com/youtube/v3"
ANALYTICS = "https://youtubeanalytics.googleapis.com/v2/reports"
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly", "https://www.googleapis.com/auth/yt-analytics.readonly"]


def now():
    return datetime.now(timezone.utc)


def iso_dur(s):
    m_ = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    if not m_:
        return None
    d, h, mi, se = (int(x or 0) for x in m_.groups())
    return d * 86400 + h * 3600 + mi * 60 + se


def _key(db):
    p = registry.get(db, "youtube_data")
    p.need()
    return p.creds["api_key"]


# ------------------------------------------------------------------ public data
def _store_videos(db, items):
    out = []
    for v in items:
        sn, stt, cd = v.get("snippet", {}), v.get("statistics", {}), v.get("contentDetails", {})
        ch = db.query(m.Channel).filter_by(youtube_channel_id=sn.get("channelId")).one_or_none()
        if ch is None and sn.get("channelId"):
            ch = m.Channel(youtube_channel_id=sn["channelId"], title=sn.get("channelTitle", ""))
            db.add(ch)
            db.flush()
        row = db.query(m.Video).filter_by(youtube_video_id=v["id"]).one_or_none() or m.Video(youtube_video_id=v["id"])
        row.channel_id = ch.id if ch else None
        row.title, row.description = sn.get("title", ""), (sn.get("description") or "")[:5000]
        row.published_at = datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00")) if sn.get("publishedAt") else None
        row.duration_s = iso_dur(cd.get("duration"))
        row.view_count = int(stt["viewCount"]) if "viewCount" in stt else None  # hidden counts stay None, never 0
        row.like_count = int(stt["likeCount"]) if "likeCount" in stt else None
        row.comment_count = int(stt["commentCount"]) if "commentCount" in stt else None
        row.tags, row.snapshot_at, row.source = sn.get("tags", [])[:30], now(), "youtube_data_api"
        db.add(row)
        db.flush()
        if ch and row.view_count is not None:
            db.add(m.ChannelMetric(channel_id=ch.id, video_id=v["id"], metric="views", value=row.view_count, source="youtube_data_api", scope="public"))
        out.append(row)
    return out


def videos_by_ids(db, ids):
    key, out = _key(db), []
    for i in range(0, len(ids), 50):
        j = http("GET", API + "/videos", params={"part": "snippet,statistics,contentDetails", "id": ",".join(ids[i:i + 50]), "key": key}).json()
        out += _store_videos(db, j.get("items", []))
    return out


def search(db, q, n=25, order="relevance", published_after_days=None):
    params = {"part": "snippet", "q": q, "type": "video", "maxResults": min(50, n), "order": order, "key": _key(db)}
    if published_after_days:
        params["publishedAfter"] = (now() - timedelta(days=published_after_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    j = http("GET", API + "/search", params=params).json()
    ids = [it["id"]["videoId"] for it in j.get("items", []) if it.get("id", {}).get("videoId")]
    return videos_by_ids(db, ids)


def channel(db, ref):
    """ref: channel id (UC…), @handle or channel URL."""
    key = _key(db)
    ref = ref.strip()
    mm = re.search(r"(UC[\w-]{22})", ref)
    params = {"part": "snippet,statistics,contentDetails", "key": key}
    if mm:
        params["id"] = mm.group(1)
    else:
        h = re.search(r"@([\w.-]+)", ref)
        params["forHandle"] = "@" + (h.group(1) if h else ref.lstrip("@"))
    j = http("GET", API + "/channels", params=params).json()
    if not j.get("items"):
        raise ProviderError("Channel not found", retryable=False)
    c = j["items"][0]
    row = db.query(m.Channel).filter_by(youtube_channel_id=c["id"]).one_or_none() or m.Channel(youtube_channel_id=c["id"])
    row.title = c["snippet"]["title"]
    stt = c.get("statistics", {})
    row.meta = {"description": c["snippet"].get("description", "")[:2000], "subscribers": None if stt.get("hiddenSubscriberCount") else int(stt.get("subscriberCount", 0)),
                "videos": int(stt.get("videoCount", 0)), "views": int(stt.get("viewCount", 0)), "uploads": c.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads"),
                "thumbnail": c["snippet"].get("thumbnails", {}).get("medium", {}).get("url")}
    row.last_synced_at = now()
    db.add(row)
    db.flush()
    for k in ("subscribers", "views", "videos"):
        if row.meta.get(k) is not None:
            db.add(m.ChannelMetric(channel_id=row.id, metric="channel_" + k, value=row.meta[k], source="youtube_data_api", scope="public"))
    return row


def channel_videos(db, ch, n=50, token=None):
    pl = (ch.meta or {}).get("uploads")
    if not pl:
        return []
    params = {"part": "contentDetails", "playlistId": pl, "maxResults": 50}
    headers = {}
    if token:
        headers["authorization"] = "Bearer " + token
    else:
        params["key"] = _key(db)
    ids, page = [], None
    while len(ids) < n:
        if page:
            params["pageToken"] = page
        j = http("GET", API + "/playlistItems", params=params, headers=headers).json()
        ids += [it["contentDetails"]["videoId"] for it in j.get("items", [])]
        page = j.get("nextPageToken")
        if not page:
            break
    return videos_by_ids(db, ids[:n]) if not token else _own_videos(db, ids[:n], token)


def _own_videos(db, ids, token):
    out = []
    for i in range(0, len(ids), 50):
        j = http("GET", API + "/videos", params={"part": "snippet,statistics,contentDetails", "id": ",".join(ids[i:i + 50])}, headers={"authorization": "Bearer " + token}).json()
        out += _store_videos(db, j.get("items", []))
    return out


# ------------------------------------------------------------------ analysis
def features(v):
    t = v.title or ""
    age_days = max(1.0, (now() - v.published_at).total_seconds() / 86400) if v.published_at else None
    return {"id": v.youtube_video_id, "title": t, "channel_id": str(v.channel_id) if v.channel_id else None, "views": v.view_count, "likes": v.like_count,
            "comments": v.comment_count, "duration_min": round(v.duration_s / 60, 1) if v.duration_s else None, "age_days": round(age_days, 1) if age_days else None,
            "views_per_day": round(v.view_count / age_days, 1) if v.view_count is not None and age_days else None, "title_len": len(t), "has_number": bool(re.search(r"\d", t)),
            "is_question": "?" in t, "caps_words": sum(1 for w in t.split() if len(w) > 2 and w.isupper()), "published": v.published_at.date().isoformat() if v.published_at else None}


def outliers(db, vids):
    """Views relative to each channel's own median (needs ≥3 videos from the channel in the set or in the DB)."""
    out = []
    for v in vids:
        if v.view_count is None or not v.channel_id:
            continue
        peers = [x.view_count for x in db.query(m.Video).filter(m.Video.channel_id == v.channel_id, m.Video.view_count.isnot(None)).all()]
        if len(peers) >= 3:
            med = statistics.median(peers)
            if med > 0:
                out.append((v, round(v.view_count / med, 2)))
    return sorted(out, key=lambda x: -x[1])


def public_report(db, query, n=30, days=None, project_id=None):
    vids = search(db, query, n, "relevance", days)
    for chid in {v.channel_id for v in vids if v.channel_id}:
        ch = db.get(m.Channel, chid)
        try:
            if ch and not (ch.meta or {}).get("uploads"):
                channel(db, ch.youtube_channel_id)
        except ProviderError:
            pass
    feats = [features(v) for v in vids]
    vpd = [f["views_per_day"] for f in feats if f["views_per_day"] is not None]
    stats = {"videos": len(feats), "median_views_per_day": statistics.median(vpd) if vpd else None,
             "median_duration_min": statistics.median([f["duration_min"] for f in feats if f["duration_min"]]) if any(f["duration_min"] for f in feats) else None,
             "share_with_numbers": round(sum(f["has_number"] for f in feats) / len(feats), 2) if feats else None,
             "share_questions": round(sum(f["is_question"] for f in feats) / len(feats), 2) if feats else None}
    outs = [{"id": v.youtube_video_id, "title": v.title, "ratio_to_channel_median": r} for v, r in outliers(db, vids)[:10]]
    words = {}
    for f in feats:
        for w in re.findall(r"[a-z]{4,}", f["title"].lower()):
            words[w] = words.get(w, 0) + 1
    stats["frequent_title_words"] = sorted(words.items(), key=lambda x: -x[1])[:20]
    table = "\n".join("%s | %s views | %s/day | %s min | %s" % (f["title"][:90], f["views"], f["views_per_day"], f["duration_min"], f["published"]) for f in feats[:30])
    try:
        summary = LLM(db, project_id, "youtube").complete(
            "You analyse public YouTube data for a creator. Use only the numbers given. Say 'associated with', never 'causes'. Public data cannot show retention or CTR. Suggest 5 concrete, evidence-based topic angles.",
            "Query: %s\nStats: %s\nOutliers vs their channel median: %s\nVideos:\n%s" % (query, stats, outs, external(table, "youtube metadata")), max_tokens=1400, temperature=0.4)
    except ProviderError as e:
        summary = "Automatic summary unavailable (%s). Raw statistics are below." % e
    rep = m.ResearchReport(project_id=project_id, kind="youtube_public", query=query, summary=summary,
                           data={"stats": stats, "outliers": outs, "videos": feats, "retrieved_at": now().isoformat(), "source": "YouTube Data API v3 (public)"})
    db.add(rep)
    db.flush()
    ingest(db, "YouTube research '%s' (%s): %s" % (query, date.today().isoformat(), summary), "YouTube: " + query, "youtube", project_id, "inferred",
           None, {"report_id": str(rep.id)}, expires_at=now() + timedelta(days=30))
    return rep


# ------------------------------------------------------------------ OAuth (owner's channel)
def _oauth(db):
    p = registry.get(db, "google_oauth")
    s = get_settings()
    cid = p.creds.get("client_id") or s.google_client_id
    sec = p.creds.get("client_secret") or s.google_client_secret
    if not cid or not sec:
        raise NotConfigured("Google OAuth client ID and secret are not configured (Settings → Providers → Google OAuth)")
    return cid, sec


def _ser():
    return URLSafeTimedSerializer(get_settings().secret_key, salt="fda-oauth")


def redirect_uri():
    return get_settings().public_base_url.rstrip("/") + "/api/v1/youtube/oauth/callback"


def auth_url(db, user_id):
    cid, _ = _oauth(db)
    state = _ser().dumps({"u": str(user_id), "t": time.time()})
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": redirect_uri(), "response_type": "code", "scope": " ".join(SCOPES), "access_type": "offline",
        "include_granted_scopes": "true", "prompt": "consent", "state": state})


def callback(db, code, state):
    try:
        st = _ser().loads(state, max_age=900)
    except BadSignature:
        raise ProviderError("Invalid or expired OAuth state", retryable=False)
    cid, sec = _oauth(db)
    tok = http("POST", "https://oauth2.googleapis.com/token", data={"code": code, "client_id": cid, "client_secret": sec, "redirect_uri": redirect_uri(),
                                                                    "grant_type": "authorization_code"}).json()
    conn = db.query(m.ChannelConnection).filter_by(user_id=st["u"]).first() or m.ChannelConnection(user_id=st["u"])
    _save_token(conn, tok)
    conn.scopes, conn.status, conn.last_error = tok.get("scope", ""), "connected", None
    db.add(conn)
    db.flush()
    me = http("GET", API + "/channels", params={"part": "snippet,statistics,contentDetails", "mine": "true"}, headers={"authorization": "Bearer " + tok["access_token"]}).json()
    if me.get("items"):
        c = me["items"][0]
        ch = db.query(m.Channel).filter_by(youtube_channel_id=c["id"]).one_or_none() or m.Channel(youtube_channel_id=c["id"])
        ch.title, ch.is_own = c["snippet"]["title"], True
        ch.meta = {"uploads": c.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads"), "thumbnail": c["snippet"].get("thumbnails", {}).get("medium", {}).get("url")}
        db.add(ch)
        db.flush()
        conn.channel_id = ch.id
    return conn


def _save_token(conn, tok):
    old = decrypt(conn.token_encrypted) if conn.token_encrypted else {}
    if "refresh_token" not in tok and old.get("refresh_token"):
        tok["refresh_token"] = old["refresh_token"]
    conn.token_encrypted = encrypt(tok)
    conn.expires_at = now() + timedelta(seconds=int(tok.get("expires_in", 3600)) - 60)


def access_token(db, conn):
    tok = decrypt(conn.token_encrypted)
    if not tok:
        raise NotConfigured("YouTube channel is not connected")
    if conn.expires_at and conn.expires_at > now():
        return tok["access_token"]
    cid, sec = _oauth(db)
    if not tok.get("refresh_token"):
        conn.status = "expired"
        raise NotConfigured("YouTube authorisation expired; reconnect the channel")
    try:
        new = http("POST", "https://oauth2.googleapis.com/token", data={"client_id": cid, "client_secret": sec, "refresh_token": tok["refresh_token"], "grant_type": "refresh_token"}).json()
    except ProviderError as e:
        conn.status, conn.last_error = "expired", str(e)[:300]
        raise NotConfigured("YouTube authorisation could not be refreshed; reconnect the channel (%s)" % e)
    _save_token(conn, new)
    return new["access_token"]


def _report(token, params):
    j = http("GET", ANALYTICS, params=params, headers={"authorization": "Bearer " + token}).json()
    cols = [c["name"] for c in j.get("columnHeaders", [])]
    return [dict(zip(cols, r)) for r in j.get("rows", [])]


CHANNEL_METRICS = "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,subscribersLost,likes,comments,shares"


def sync_analytics(db, user_id, days=90):
    conn = db.query(m.ChannelConnection).filter_by(user_id=user_id, status="connected").first()
    if not conn or not conn.channel_id:
        raise NotConfigured("Connect your YouTube channel first")
    token = access_token(db, conn)
    ch = db.get(m.Channel, conn.channel_id)
    end = date.today()
    start = end - timedelta(days=days)
    base = {"ids": "channel==MINE", "startDate": start.isoformat(), "endDate": end.isoformat()}
    unavailable, n = [], 0

    def put(metric, value, vid=None, day=None, dim=None, ps=None, pe=None):
        nonlocal n
        if value is None:
            return
        db.add(m.ChannelMetric(channel_id=ch.id, video_id=vid, metric=metric, value=float(value), dimension=dim,
                               period_start=ps or (datetime.fromisoformat(day).replace(tzinfo=timezone.utc) if day else datetime.combine(start, datetime.min.time(), timezone.utc)),
                               period_end=pe or (datetime.fromisoformat(day).replace(tzinfo=timezone.utc) if day else datetime.combine(end, datetime.min.time(), timezone.utc)),
                               source="youtube_analytics_api", scope="authorized"))
        n += 1
    try:
        for r in _report(token, dict(base, metrics=CHANNEL_METRICS, dimensions="day", sort="day")):
            for k, v in r.items():
                if k != "day":
                    put(k, v, day=r["day"])
    except ProviderError as e:
        unavailable.append("daily channel metrics: %s" % str(e)[:160])
    try:
        for r in _report(token, dict(base, metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,likes",
                                     dimensions="video", sort="-views", maxResults=200)):
            for k, v in r.items():
                if k != "video":
                    put(k, v, vid=r["video"])
    except ProviderError as e:
        unavailable.append("per-video metrics: %s" % str(e)[:160])
    try:
        for r in _report(token, dict(base, metrics="views,estimatedMinutesWatched", dimensions="insightTrafficSourceType")):
            put("views", r["views"], dim="traffic:" + r["insightTrafficSourceType"])
            put("estimatedMinutesWatched", r["estimatedMinutesWatched"], dim="traffic:" + r["insightTrafficSourceType"])
    except ProviderError as e:
        unavailable.append("traffic sources: %s" % str(e)[:160])
    top = [r.video_id for r in db.query(m.ChannelMetric).filter_by(channel_id=ch.id, metric="views", scope="authorized").filter(m.ChannelMetric.video_id.isnot(None))
           .order_by(m.ChannelMetric.value.desc()).limit(10).all()]
    for vid in top:
        try:
            for r in _report(token, dict(base, metrics="audienceWatchRatio,relativeRetentionPerformance", dimensions="elapsedVideoTimeRatio", filters="video==" + vid)):
                put("audienceWatchRatio", r.get("audienceWatchRatio"), vid=vid, dim="retention:%.2f" % float(r["elapsedVideoTimeRatio"]))
                put("relativeRetentionPerformance", r.get("relativeRetentionPerformance"), vid=vid, dim="retention:%.2f" % float(r["elapsedVideoTimeRatio"]))
        except ProviderError as e:
            unavailable.append("retention for %s: %s" % (vid, str(e)[:100]))
            break
    unavailable.append("impressions and click-through rate are not exposed by the YouTube Analytics API v2 (they are only in YouTube Studio / the Reporting API)")
    try:
        channel_videos(db, ch, 100, token)
    except ProviderError as e:
        unavailable.append("video list: %s" % str(e)[:120])
    ch.last_synced_at = now()
    ch.meta = dict(ch.meta or {}, unavailable=unavailable, last_sync_rows=n)
    return {"rows": n, "unavailable": unavailable}


def own_analysis(db, user_id, project_id=None):
    ch = db.query(m.Channel).filter_by(is_own=True).first()
    if not ch:
        raise NotConfigured("No connected channel")
    rows = db.query(m.ChannelMetric).filter_by(channel_id=ch.id, scope="authorized").filter(m.ChannelMetric.video_id.isnot(None), m.ChannelMetric.dimension.is_(None)).all()
    per = {}
    for r in rows:
        per.setdefault(r.video_id, {})[r.metric] = r.value
    vids = {v.youtube_video_id: v for v in db.query(m.Video).filter(m.Video.youtube_video_id.in_(list(per))).all()}
    table = []
    for vid, mt in per.items():
        v = vids.get(vid)
        f = features(v) if v else {"id": vid, "title": "(unknown)"}
        f.update({k: mt.get(k) for k in ("views", "averageViewPercentage", "averageViewDuration", "subscribersGained", "estimatedMinutesWatched")})
        table.append(f)
    table.sort(key=lambda r: -(r.get("views") or 0))

    def corr(xk, yk):
        pts = [(float(r[xk]), float(r[yk])) for r in table if r.get(xk) is not None and r.get(yk) is not None]
        if len(pts) < 5:
            return None
        try:
            return round(statistics.correlation([p[0] for p in pts], [p[1] for p in pts]), 2)
        except statistics.StatisticsError:
            return None
    cors = {"duration_vs_avg_view_pct": corr("duration_min", "averageViewPercentage"), "title_len_vs_views": corr("title_len", "views"),
            "has_number_vs_views": corr("has_number", "views"), "question_vs_views": corr("is_question", "views")}
    txt = "\n".join("%s | views %s | avg %% viewed %s | %s min" % (r["title"][:80], r.get("views"), r.get("averageViewPercentage"), r.get("duration_min")) for r in table[:40])
    try:
        summary = LLM(db, project_id, "youtube").complete(
            "You analyse a creator's own YouTube analytics. Compare strong and weak videos, describe patterns as associations (not causes), mention sample size, and give 5 evidence-based next-video suggestions.",
            "Correlations (Pearson, n small): %s\nVideos:\n%s" % (cors, external(txt, "analytics")), max_tokens=1400, temperature=0.4)
    except ProviderError as e:
        summary = "Automatic summary unavailable (%s)." % e
    rep = m.ResearchReport(project_id=project_id, kind="youtube_channel", query="Own channel analysis: " + ch.title, summary=summary,
                           data={"correlations": cors, "videos": table[:100], "retrieved_at": now().isoformat(), "unavailable": (ch.meta or {}).get("unavailable", []),
                                 "source": "YouTube Analytics API (authorised, read-only)"})
    db.add(rep)
    db.flush()
    from fda.memory.store import remember
    try:
        remember(db, user_id, "performance", "channel_analysis", summary[:3000], {"report_id": str(rep.id), "correlations": cors}, "inferred", "youtube_analytics")
    except Exception:
        pass
    return rep
