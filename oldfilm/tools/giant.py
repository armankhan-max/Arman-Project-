"""Composite a giant silhouette into a sea plate.
usage: python giant.py specs.json
spec: {out, bg, horizon (frac y of sea surface where giant stands), fig, cut (frac y in fig image
       = waterline on the figure), x (frac center in bg), h (giant height above water, frac of bg H),
       haze (0..1), flip (bool), thr (mask threshold), night (bool), dark (float)}"""
import json, sys, numpy as np, cv2

OW = 1920

def load(p):
    im = cv2.imread(p, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
    return im

def comp(s):
    bg = load(s["bg"])
    bh, bw = bg.shape
    sc = OW / bw
    bg = cv2.resize(bg, (OW, int(bh * sc)), interpolation=cv2.INTER_CUBIC)
    H, W = bg.shape
    fig = load(s["fig"])
    if s.get("flip"): fig = fig[:, ::-1]
    fh, fw = fig.shape
    cut = int(s["cut"] * fh)
    # background estimate of the fig image (sky): heavy blur of max filter
    skyrow = np.percentile(fig, 80, axis=1)[:, None]
    skyrow = cv2.GaussianBlur(skyrow.astype(np.float32), (1, 0), sigmaX=0.1, sigmaY=9)
    thr = s.get("thr", 0.22)
    diff = skyrow - fig
    m = np.clip((diff - thr) / 0.1, 0, 1)
    m[cut:] = 0
    hard = (m > 0.5).astype(np.uint8)
    hard = cv2.morphologyEx(hard, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n_, lab, stats, _ = cv2.connectedComponentsWithStats(hard)
    cand = [i for i in range(1, n_) if stats[i, cv2.CC_STAT_LEFT] > 3 and stats[i, cv2.CC_STAT_LEFT] + stats[i, cv2.CC_STAT_WIDTH] < fw - 3 and stats[i, cv2.CC_STAT_TOP] > 3]
    if not cand: cand = list(range(1, n_))
    kk = max(cand, key=lambda i: stats[i, cv2.CC_STAT_AREA])
    blob = (lab == kk).astype(np.uint8)
    cnts, _ = cv2.findContours(blob, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    filled = np.zeros_like(blob); cv2.drawContours(filled, cnts, -1, 1, -1)
    m = cv2.GaussianBlur(filled.astype(np.float32), (0, 0), 1.0)
    m[cut:] = 0
    ys, xs = np.where(m > 0.5)
    top = ys.min(); x0, x1 = xs.min(), xs.max()
    pad = 12
    y0 = max(0, top - pad)
    xa, xb = max(0, x0 - pad), min(fw, x1 + pad)
    fig_c = fig[y0:cut, xa:xb]; m_c = m[y0:cut, xa:xb]
    # scale so that head->waterline = h * H
    target = s["h"] * H
    k = target / (cut - top)
    nh, nw = int(fig_c.shape[0] * k), int(fig_c.shape[1] * k)
    fig_c = cv2.resize(fig_c, (nw, nh), interpolation=cv2.INTER_CUBIC)
    m_c = cv2.resize(m_c, (nw, nh), interpolation=cv2.INTER_CUBIC)
    m_c = cv2.GaussianBlur(m_c, (0, 0), 1.2 + k * 0.4)
    # silhouette tone: dark, then hazed toward local sky value
    hy = int(s["horizon"] * H)
    cx = int(s["x"] * W)
    px0 = cx - nw // 2; py0 = hy - nh
    # local sky tone above horizon at giant position
    region = bg[max(0, hy - int(0.35 * H)):hy, max(0, px0):min(W, px0 + nw)]
    skyv = float(np.percentile(region, 70)) if region.size else 0.8
    dark = s.get("dark", 0.10)
    body = dark + 0.25 * (fig_c - fig_c.min())  # keep a little internal modelling
    haze = s.get("haze", 0.3)
    # vertical haze gradient: lower body slightly more hazed (mist on water)
    g = np.linspace(0, 1, nh, dtype=np.float32)[:, None]
    hz = np.clip(haze + 0.18 * g ** 3, 0, 0.9)
    body = body * (1 - hz) + skyv * hz
    out = bg.copy()
    # paste with clipping
    ya, yb = max(0, py0), min(H, py0 + nh)
    xa2, xb2 = max(0, px0), min(W, px0 + nw)
    sy, sx = ya - py0, xa2 - px0
    B = body[sy:sy + (yb - ya), sx:sx + (xb2 - xa2)]
    M = m_c[sy:sy + (yb - ya), sx:sx + (xb2 - xa2)]
    # soft waterline: fade last few px
    fadepx = max(3, int(nh * s.get("fade", 0.02)))
    fl = np.ones_like(M); fl[-fadepx:] = np.linspace(1, s.get("fade_to", 0.2), fadepx)[:, None] ** 1.5
    M = M * fl
    out[ya:yb, xa2:xb2] = out[ya:yb, xa2:xb2] * (1 - M) + B * M
    # reflection
    rh = int(nh * 0.45)
    if rh > 4 and hy < H:
        ref = body[::-1][:rh]; rm = m_c[::-1][:rh] * np.linspace(0.45, 0, rh)[:, None]
        yy = np.arange(rh)[:, None]
        shift = (np.sin(yy * 0.35) * 3 * (1 + yy / rh * 3)).astype(np.float32)
        mapx = (np.arange(nw)[None, :] + shift).astype(np.float32)
        mapy = np.repeat(yy, nw, 1).astype(np.float32)
        ref = cv2.remap(ref.astype(np.float32), mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        rm = cv2.remap(rm.astype(np.float32), mapx, mapy, cv2.INTER_LINEAR)
        ra, rb = hy, min(H, hy + rh)
        R = ref[:rb - ra, sx:sx + (xb2 - xa2)]; RM = rm[:rb - ra, sx:sx + (xb2 - xa2)]
        out[ra:rb, xa2:xb2] = out[ra:rb, xa2:xb2] * (1 - RM) + R * RM
    # swell / foam line around the body at waterline
    if s.get("foam", True):
        wl = np.zeros_like(out)
        wcx0, wcx1 = max(0, px0 - int(nw * 0.25)), min(W, px0 + nw + int(nw * 0.25))
        cv2.ellipse(wl, (cx, hy), (int(nw * 0.42), max(2, int(nh * 0.008))), 0, 0, 360, 1.0, -1)
        wl = cv2.GaussianBlur(wl, (0, 0), max(1.5, nh * 0.006))
        out = np.clip(out + wl * 0.12, 0, 1)
    # re-paste foreground boats/objects that must stay in front (mask from bg darker than sea below horizon)
    for fgbox in s.get("keep_fg", []):
        x0_, y0_, x1_, y1_ = [int(v * (W if i % 2 == 0 else H)) for i, v in enumerate(fgbox)]
        out[y0_:y1_, x0_:x1_] = bg[y0_:y1_, x0_:x1_]
    if s.get("night"):
        out = out * s.get("night_k", 0.6)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    for gx, gy, gr, gi in s.get("glow", []):
        gx, gy, gr = gx * W, gy * H, gr * W
        d2 = ((xx - gx) ** 2 + (yy - gy) ** 2) / (gr * gr)
        out = out + gi * np.exp(-d2) + 0.6 * gi * np.exp(-d2 * 40)
        # glint on water below the lamp
        dw = ((xx - gx) / (gr * 0.6)) ** 2 + ((yy - gy - 3 * gr) / (gr * 4)) ** 2
        out = out + 0.25 * gi * np.exp(-dw) * (yy > gy)
    out = np.clip(out, 0, 1)
    cv2.imwrite(s["out"], np.clip(out * 255, 0, 255).astype(np.uint8))
    print("wrote", s["out"])

if __name__ == "__main__":
    for s in json.load(open(sys.argv[1])):
        comp(s)
