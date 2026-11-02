import React from 'react';
import {Composition, staticFile, continueRender, delayRender} from 'remotion';
import {loadFont} from '@remotion/fonts';
import {Main} from './Main';
import {FPS, TOTAL_FRAMES} from './timeline';

const h = delayRender('font');
loadFont({family: 'Baloo2', url: staticFile('Baloo2-ExtraBold.woff2'), weight: '800'}).then(() => continueRender(h)).catch(() => continueRender(h));

export const Root: React.FC = () => (
  <Composition id="Main" component={Main} durationInFrames={TOTAL_FRAMES} fps={FPS} width={1080} height={1920} />
);
