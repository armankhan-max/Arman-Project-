import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {SCENES, TOTAL_FRAMES} from './timeline';
import {Defs, Trans} from './lib/stage';
import {Captions} from './components/Caption';
import {SceneProps} from './scenes/common';
import {S1} from './scenes/S1';
import {S2} from './scenes/S2';
import {S3} from './scenes/S3';
import {S4} from './scenes/S4';
import {S5} from './scenes/S5';
import {S6} from './scenes/S6';
import {S7} from './scenes/S7';
import {S8} from './scenes/S8';

const MAP: Record<string, {C: React.FC<SceneProps>; tin: Trans; tout: Trans}> = {
  S1: {C: S1, tin: 'cut', tout: 'action'},
  S2: {C: S2, tin: 'action', tout: 'whip'},
  S3: {C: S3, tin: 'whip', tout: 'whip'},
  S4: {C: S4, tin: 'whip', tout: 'match'},
  S5: {C: S5, tin: 'match', tout: 'whip'},
  S6: {C: S6, tin: 'whip', tout: 'action'},
  S7: {C: S7, tin: 'action', tout: 'whip'},
  S8: {C: S8, tin: 'whip', tout: 'cut'},
};

export const Main: React.FC = () => {
  const g = Math.min(useCurrentFrame(), TOTAL_FRAMES - 1);
  const sc = SCENES.find((s) => g >= s.from && g < s.to) ?? SCENES[SCENES.length - 1];
  const {C, tin, tout} = MAP[sc.id];
  return (
    <AbsoluteFill style={{backgroundColor: '#CDE3F4'}}>
      <svg width={1080} height={1920} viewBox="0 0 1080 1920" style={{position: 'absolute', inset: 0}}>
        <Defs />
        <C f={g - sc.from} dur={sc.to - sc.from} tin={tin} tout={tout} g={g} />
        <rect x={0} y={0} width={1080} height={1920} fill="url(#vignette)" pointerEvents="none" />
        <Captions g={g} />
      </svg>
    </AbsoluteFill>
  );
};
