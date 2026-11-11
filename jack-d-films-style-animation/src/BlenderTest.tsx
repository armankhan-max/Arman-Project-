import React from "react";
import { useGLTF } from "@react-three/drei";
import { ThreeCanvas } from "@remotion/three";
import { AbsoluteFill, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

// Model built by blender/build_test.py -> public/models/blender-test.glb
const MODEL = staticFile("models/blender-test.glb");
useGLTF.preload(MODEL, false);

const Model: React.FC = () => {
  const frame = useCurrentFrame();
  const { scene } = useGLTF(MODEL, false);
  const rot = interpolate(frame, [0, 90], [-0.6, 0.6]);
  return <primitive object={scene} rotation={[0, rot, 0]} />;
};

export const BlenderTest: React.FC = () => {
  const { width, height } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: "#f4ecd8" }}>
      <ThreeCanvas width={width} height={height} camera={{ position: [0, 0.4, 5], fov: 45 }}>
        <ambientLight intensity={0.7} />
        <directionalLight position={[4, 6, 5]} intensity={2.4} />
        <React.Suspense fallback={null}>
          <Model />
        </React.Suspense>
      </ThreeCanvas>
    </AbsoluteFill>
  );
};
