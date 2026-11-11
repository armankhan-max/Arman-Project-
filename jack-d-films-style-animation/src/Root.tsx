import React from "react";
import { Composition } from "remotion";
import { BlenderTest } from "./BlenderTest";
import { SetupTest } from "./SetupTest";

export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="SetupTest"
        component={SetupTest}
        durationInFrames={90}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
      />
      <Composition
        id="BlenderTest"
        component={BlenderTest}
        durationInFrames={90}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
      />
    </>
  );
};
