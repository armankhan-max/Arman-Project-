import {Trans} from '../lib/stage';
export type SceneProps = {f: number; dur: number; tin: Trans; tout: Trans; g: number};
/** gentle handheld drift (+-8px sine) so the camera is never static */
export const drift = (f: number, a = 8) => [Math.sin(f / 47) * a, Math.cos(f / 61) * a] as const;
