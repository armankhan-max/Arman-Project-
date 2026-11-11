import React from "react";
import { ThreeCanvas } from "@remotion/three";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// Minimal scene that proves Remotion + Three.js render together. Replace with real scenes.
const Scene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame, fps, config: { damping: 12 } });
  const rot = interpolate(frame, [0, 90], [0, Math.PI * 2]);

  return (
    <>
      <ambientLight intensity={0.6} />
      <directionalLight position={[4, 6, 5]} intensity={2.2} castShadow />
      <mesh rotation={[0.5, rot, 0]} scale={pop} castShadow>
        <boxGeometry args={[1.6, 1.6, 1.6]} />
        <meshStandardMaterial color="#ff5a3c" roughness={0.45} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1.6, 0]} receiveShadow>
        <planeGeometry args={[30, 30]} />
        <meshStandardMaterial color="#f4ecd8" />
      </mesh>
    </>
  );
};

export const SetupTest: React.FC = () => {
  const { width, height } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: "#f4ecd8" }}>
      <ThreeCanvas width={width} height={height} shadows camera={{ position: [0, 1.5, 6], fov: 45 }}>
        <Scene />
      </ThreeCanvas>
    </AbsoluteFill>
  );
};
