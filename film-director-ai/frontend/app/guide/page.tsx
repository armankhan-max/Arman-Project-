"use client";
import Link from "next/link";

const STEPS: [string, string][] = [
  ["1. Pick an idea", "Use Creator tools → Idea lab or Title lab, or start from a template on the New project form."],
  ["2. Create the video", "Projects → New project (one video) or Bulk create (up to 50 titles at once). Choose the style, length, language and shape. Upload your own narration if you have one; it is kept exactly as recorded."],
  ["3. Let the Director work", "Research, script, narration, storyboard, stock footage search, music, sound effects, captions, render and quality check run by themselves. Watch progress in Job queue."],
  ["4. Review", "Open the project: play the video, read the QC report, check every scene on the Storyboard tab."],
  ["5. Fix anything", "Chat with the Director (“Scene 4 ka camera change kar”, “music thoda lower kar”), rewrite the script with AI script tools, or open the Editor, select a clip and use “Find stock footage” to swap the picture. Press Apply & render."],
  ["6. Publish", "Upload pack tab: titles, description with chapters, tags, hashtags, pinned comment and thumbnails. Renders tab: download the MP4 or make a vertical Short. Make a Hindi / English / Hinglish version from the header."],
];
const TIPS: [string, string][] = [
  ["More real footage", "Add free Pexels and Pixabay keys in Settings → Providers. Wikimedia, NASA, Openverse and Internet Archive already work without keys."],
  ["Better writing", "Add an Anthropic or OpenAI key (and a budget) for stronger scripts and storyboards than the free model."],
  ["Same host every time", "Save an AI host on the Characters page: one face, one voice, one personality, reused in every avatar video."],
  ["Real lip sync", "Add a HeyGen key to turn the host photo into a true lip-synced talking video."],
  ["Spending", "Paid providers never run without a daily or monthly limit. As owner you can switch on unlimited mode in Settings → Budget."],
  ["Captions", "Download .srt or .vtt from the Script tab and upload them to YouTube for accurate subtitles."],
];

export default function Guide() {
  return (
    <div className="flex flex-col gap-6">
      <div><h1 className="h1">How to use the studio</h1><p className="text-sm text-dim">From an idea to a finished, uploaded video.</p></div>
      <div className="grid gap-3 md:grid-cols-2">{STEPS.map(([a, b]) => <div key={a} className="card"><b>{a}</b><p className="mt-1 text-sm text-dim">{b}</p></div>)}</div>
      <h2 className="h2">Tips</h2>
      <div className="grid gap-3 md:grid-cols-3">{TIPS.map(([a, b]) => <div key={a} className="card"><b className="text-sm">{a}</b><p className="mt-1 text-xs text-dim">{b}</p></div>)}</div>
      <div className="flex flex-wrap gap-2"><Link className="btn btn-pri" href="/projects/?new=1">Make a video</Link><Link className="btn" href="/tools">Creator tools</Link><Link className="btn" href="/stock">Stock library</Link></div>
    </div>
  );
}
