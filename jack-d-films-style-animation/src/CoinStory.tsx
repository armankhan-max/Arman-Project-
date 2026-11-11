import React from "react";
import {
  AbsoluteFill,
  Audio,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import captions from "./data/captions.json";
import timeline from "./data/timeline.json";

const fontFace = `@font-face { font-family: "Cap"; src: url(${staticFile("fonts/Inter-ExtraBold.otf")}) format("opentype"); font-weight: 800; }`;

// Whip between shots: short blur + push around every cut so the camera feels continuous.
const useWhip = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  let nearest = 999;
  let sign = 1;
  timeline.cuts.forEach((c, i) => {
    const d = frame - c * fps;
    if (Math.abs(d) < Math.abs(nearest)) {
      nearest = d;
      sign = i % 2 ? 1 : -1;
    }
  });
  const k = interpolate(Math.abs(nearest), [0, 5], [1, 0], { extrapolateRight: "clamp" });
  const dir = nearest < 0 ? 1 : -1;
  return { blur: k * k * 26, shift: dir * sign * k * k * 90, zoom: 1.04 + k * 0.1 };
};

const Caption: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const cur = captions.find((c) => t >= c.s - 0.04 && t < c.e);
  if (!cur) return null;
  const pop = spring({ frame: frame - (cur.s - 0.04) * fps, fps, config: { damping: 14, stiffness: 260, mass: 0.5 } });
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center" }}>
      <div
        style={{
          marginTop: 1380,
          fontFamily: "Cap, sans-serif",
          fontWeight: 800,
          fontSize: 78,
          color: "white",
          letterSpacing: -1,
          textAlign: "center",
          padding: "0 60px",
          transform: `scale(${0.82 + 0.18 * pop})`,
          WebkitTextStroke: "10px #111",
          paintOrder: "stroke fill",
          textShadow: "0 8px 22px rgba(0,0,0,0.65)",
        }}
      >
        {cur.text}
      </div>
    </AbsoluteFill>
  );
};

export const CoinStory: React.FC = () => {
  const { blur, shift, zoom } = useWhip();
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <style>{fontFace}</style>
      <AbsoluteFill
        style={{
          transform: `translateX(${shift}px) scale(${zoom})`,
          filter: `blur(${blur}px) contrast(1.07) saturate(1.22)`,
        }}
      >
        <OffthreadVideo src={staticFile("shots/base.mp4")} style={{ width: "100%", height: "100%", objectFit: "cover" }} muted />
      </AbsoluteFill>
      <AbsoluteFill
        style={{ background: "radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.42) 100%)" }}
      />
      <Caption />
      <Audio src={staticFile("audio/vo.mp3")} />
      <Audio src={staticFile("audio/sfx.wav")} volume={0.55} />
    </AbsoluteFill>
  );
};
