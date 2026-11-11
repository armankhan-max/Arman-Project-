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

type Trans = "zoom" | "flash" | "slide" | "slideUp" | "flip";
// Transition used at the cut between shot i and shot i + 1.
const TRANS: Trans[] = [
  "flash", "zoom", "zoom", "flip", "slide", "zoom", "slideUp", "slide",
  "flip", "zoom", "flash", "zoom", "slide", "flash", "zoom", "flip",
];
const { H, shots } = timeline;
const fontFace = `@font-face { font-family: "Cap"; src: url(${staticFile("fonts/Inter-ExtraBold.otf")}) format("opentype"); font-weight: 800; }`;
const clamp01 = (v: number) => Math.min(1, Math.max(0, v));
const ease = (p: number) => p * p * (3 - 2 * p);
// 0..1 across the 2H-frame window centred on a cut; real frames exist on both sides (handles).
const progress = (frame: number, cut: number) => clamp01((frame - (cut - H)) / (2 * H));

const Shot: React.FC<{ index: number }> = ({ index }) => {
  const frame = useCurrentFrame() + shots[index].start - H; // back to global time
  const last = index === shots.length - 1;
  const pIn = index === 0 ? 1 : progress(frame, shots[index].start);
  const pOut = last ? 0 : progress(frame, shots[index + 1].start);
  let opacity = 1;
  let scale = 1;
  let blur = 0;
  let tx = 0;
  let ty = 0;
  let ry = 0;
  if (pIn < 1) {
    const t = TRANS[index - 1];
    const e = ease(pIn);
    if (t === "zoom") {
      opacity = e; scale = 0.72 + 0.28 * e; blur = (1 - e) * 14;
    } else if (t === "flash") {
      opacity = pIn >= 0.5 ? 1 : 0;
    } else if (t === "slide") {
      tx = (1 - e) * 100; blur = Math.sin(Math.PI * pIn) * 5;
    } else if (t === "slideUp") {
      ty = (1 - e) * 100; blur = Math.sin(Math.PI * pIn) * 5;
    } else {
      opacity = pIn >= 0.5 ? 1 : 0; ry = -90 + ease(clamp01((pIn - 0.5) * 2)) * 90;
    }
  }
  if (pOut > 0) {
    const t = TRANS[index];
    const e = ease(pOut);
    if (t === "zoom") {
      scale = 1 + 0.7 * e; blur = e * 14;
    } else if (t === "flash") {
      opacity = pOut < 0.5 ? 1 : 0;
    } else if (t === "slide") {
      tx = -e * 100; blur = Math.sin(Math.PI * pOut) * 5;
    } else if (t === "slideUp") {
      ty = -e * 100; blur = Math.sin(Math.PI * pOut) * 5;
    } else {
      opacity = pOut < 0.5 ? 1 : 0; ry = ease(clamp01(pOut * 2)) * 90;
    }
  }
  return (
    <AbsoluteFill style={{ perspective: 1400 }}>
      <AbsoluteFill
        style={{
          opacity,
          transform: `translate(${tx}%, ${ty}%) rotateY(${ry}deg) scale(${scale})`,
          filter: blur > 0.05 ? `blur(${blur}px)` : undefined,
        }}
      >
        <OffthreadVideo src={staticFile(`shots/${shots[index].id}.mp4`)} style={{ width: "100%", height: "100%" }} muted />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Flash: React.FC = () => {
  const frame = useCurrentFrame();
  let o = 0;
  TRANS.forEach((t, i) => {
    if (t === "flash") {
      const p = progress(frame, shots[i + 1].start);
      if (p > 0 && p < 1) o = Math.max(o, Math.pow(1 - Math.abs(2 * p - 1), 1.4));
    }
  });
  return <AbsoluteFill style={{ backgroundColor: "white", opacity: o }} />;
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
        <Flash />
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
