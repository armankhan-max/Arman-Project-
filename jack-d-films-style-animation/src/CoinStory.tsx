import React from "react";
import {
  AbsoluteFill,
  Audio,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import captions from "./data/captions.json";
import timeline from "./data/shots.json";

// "push"     = push-through: the camera accelerates forward into the cut, the next shot comes out of the same push.
// "dissolve" = slow match dissolve (same place, time has passed).
// "none"     = the two shots were rendered as one continuous camera move, so there is nothing to hide.
type Trans = "push" | "dissolve" | "none";
// Transition at the cut between shot i and shot i + 1.
const TRANS: Trans[] = [
  "dissolve", "push", "none", "push", "push", "push", "push", "none",
  "push", "push", "push", "push", "push", "push", "push", "push",
];
const { H, shots } = timeline;
const fontFace = `@font-face { font-family: "Cap"; src: url(${staticFile("fonts/Inter-ExtraBold.otf")}) format("opentype"); font-weight: 800; }`;
const clamp01 = (v: number) => Math.min(1, Math.max(0, v));
const ease = (p: number) => p * p * (3 - 2 * p);
// 0..1 across the 2H-frame window centred on a cut; real frames exist on both sides (handles).
const progress = (frame: number, cut: number) => clamp01((frame - (cut - H)) / (2 * H));
const CREEP = 0.05;

// Shots joined by "none" share one slow creep so the camera never holds still and never jumps.
const groupSpan = (index: number) => {
  let a = index;
  let b = index;
  while (a > 0 && TRANS[a - 1] === "none") a--;
  while (b < shots.length - 1 && TRANS[b] === "none") b++;
  return [shots[a].start, shots[b].start + shots[b].n];
};

const Shot: React.FC<{ index: number }> = ({ index }) => {
  const frame = useCurrentFrame() + shots[index].start - H; // back to global time
  const last = index === shots.length - 1;
  const tIn = index === 0 ? "none" : TRANS[index - 1];
  const tOut = last ? "none" : TRANS[index];
  const cutIn = shots[index].start;
  const cutOut = last ? Infinity : shots[index + 1].start;
  const pIn = index === 0 ? 1 : progress(frame, cutIn);
  const pOut = last ? 0 : progress(frame, cutOut);
  const [g0, g1] = groupSpan(index);
  let scale = 1 + CREEP * clamp01((frame - g0) / (g1 - g0));
  let opacity = 1;
  let streak = 0; // 0..1 strength of the forward motion blur

  if (tIn === "none") {
    if (frame < cutIn) opacity = 0;
  } else if (tIn === "dissolve") {
    opacity = ease(pIn);
  } else if (pIn < 1) {
    const d = 1 - Math.pow(1 - pIn, 3); // decelerating out of the push
    scale *= 0.7 + 0.3 * d;
    streak = Math.max(streak, 1 - d);
    opacity = ease(clamp01((pIn - 0.36) / 0.2));
  }
  if (tOut === "none") {
    if (frame >= cutOut) opacity = 0;
  } else if (tOut === "dissolve") {
    scale *= 1 + 0.06 * ease(pOut);
  } else if (pOut > 0) {
    const e = Math.pow(pOut, 3); // accelerating into the cut
    scale *= 1 + 1.6 * e;
    streak = Math.max(streak, e);
    if (pOut >= 0.58) opacity = 0;
  }
  if (opacity <= 0) return null;

  const src = staticFile(`shots/${shots[index].id}.mp4`);
  const video = <OffthreadVideo src={src} style={{ width: "100%", height: "100%" }} muted />;
  const layers = streak > 0.03 ? [0, 1, 2, 3] : [0];
  return (
    <AbsoluteFill style={{ opacity }}>
      {scale < 0.999 ? (
        <AbsoluteFill style={{ transform: "scale(1.7)", filter: "blur(22px)" }}>{video}</AbsoluteFill>
      ) : null}
      {layers.map((j) => (
        <AbsoluteFill
          key={j}
          style={{
            opacity: 1 / (j + 1),
            transform: `scale(${scale * (1 + 0.07 * j * streak)})`,
            filter: streak > 0.03 ? `blur(${streak * 5}px)` : undefined,
          }}
        >
          {video}
        </AbsoluteFill>
      ))}
    </AbsoluteFill>
  );
};

const Caption: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const k = width / 1080;
  const t = frame / fps;
  const cur = captions.find((c) => t >= c.s - 0.04 && t < c.e);
  if (!cur) return null;
  const pop = spring({ frame: frame - (cur.s - 0.04) * fps, fps, config: { damping: 14, stiffness: 260, mass: 0.5 } });
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center" }}>
      <div
        style={{
          marginTop: 1380 * k,
          fontFamily: "Cap, sans-serif",
          fontWeight: 800,
          fontSize: 80 * k,
          color: "white",
          letterSpacing: -1 * k,
          textAlign: "center",
          padding: `0 ${60 * k}px`,
          transform: `scale(${0.82 + 0.18 * pop})`,
          WebkitTextStroke: `${10 * k}px #111`,
          paintOrder: "stroke fill",
          textShadow: `0 ${8 * k}px ${22 * k}px rgba(0,0,0,0.65)`,
        }}
      >
        {cur.text}
      </div>
    </AbsoluteFill>
  );
};

export const CoinStory: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const fadeIO = interpolate(frame, [0, 8, durationInFrames - 14, durationInFrames - 1], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <style>{fontFace}</style>
      <AbsoluteFill style={{ opacity: fadeIO, filter: "contrast(1.06) saturate(1.15)" }}>
        {shots.map((s, i) => (
          <Sequence key={s.id} from={s.start - H} durationInFrames={s.n + 2 * H}>
            <Shot index={i} />
          </Sequence>
        ))}
      </AbsoluteFill>
      <AbsoluteFill
        style={{ background: "radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 58%, rgba(0,0,0,0.38) 100%)" }}
      />
      <Caption />
      <Audio src={staticFile("audio/vo.mp3")} />
      <Audio src={staticFile("audio/sfx.wav")} volume={0.7} />
    </AbsoluteFill>
  );
};
