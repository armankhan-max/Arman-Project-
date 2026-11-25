#!/usr/bin/env python3
"""Find free Mixkit stock clips by topic (no API key needed).

    python3 tools/mixkit_search.py grocery snow fireplace rice
Prints "<clip id>  <title>". Use the id in project.py as  V:<id>@<offset>.
Tip: check resolution afterwards - some clips are vertical (1080x1920); avoid those.
Topic slugs that work: supermarket, rice, fireplace, cooking, winter, grocery, shopping-cart,
snow, storm, candle, oatmeal, pasta, flour, bread, oil, tea, water, soup, family, kitchen, cabin, night, lantern.
"""
import re, subprocess, sys
seen = {}
for q in sys.argv[1:]:
    html = subprocess.run(["curl", "-s", "-m", "20", f"https://mixkit.co/free-stock-video/{q}/"],
                          capture_output=True, text=True).stdout
    for m in re.finditer(r'item-id-value="(\d+)".*?alt="([^"]*)"', html, re.S):
        if m.group(1) not in seen:
            seen[m.group(1)] = m.group(2).replace("&#39;", "'")
            print(f"{m.group(1):>7}  [{q}] {seen[m.group(1)]}")
