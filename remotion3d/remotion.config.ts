import { Config } from "@remotion/cli/config";
import fs from "fs";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
// WebGL in headless Chromium (needed for Three.js). Software GL works on machines without a GPU.
Config.setChromiumOpenGlRenderer("swangle");
Config.setConcurrency(2);

// Cloud sessions ship a pre-installed Chromium; use it when present.
const preinstalled = "/opt/pw-browsers/chromium";
if (fs.existsSync(preinstalled)) {
  Config.setBrowserExecutable(preinstalled);
}
