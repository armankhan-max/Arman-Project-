import json, os
_c = json.load(open(os.path.join(os.path.dirname(__file__), "..", "cuts.json")))
def o2e(t):
    """original voice time -> edited time"""
    shift = 0.0
    for i, (a, b) in enumerate(_c["cuts"]):
        if t >= b:
            shift += (b - a) - _c["insert_silence_after_cut"].get(str(i), 0)
        elif t > a:
            return o2e(a)
    return t - shift
