// Master timeline (seconds). Picture and sound both read from here, so they never drift apart.
// Structure: cold open (night) -> rewind -> THE DAY (fast) -> THE NIGHT (each mistake comes back as a thought).
module.exports = {
  // COLD OPEN
  cold: 0, coldQ: 2.0, rew: 5.0, toDay: 7.6,
  // 1 ALARM
  alarm: 8, wake: 8.8, alarmNote: 9.6, nono: 10.2, jump: 11.2, trip: 13.0, fall: 13.4, rush: 16,
  // 2 RUSH
  hop: 16, toastS: 20, burn: 20.9, spill: 22.3, bus: 24,
  // 3 MISSED BUS
  run: 24, doors: 27.3, drive: 28.0, rain: 29.4, thunder: 29.6, ofc: 30.5, cls: 32,
  // 4 PRESENTATION
  enter: 32, point: 33.4, front: 35, frozen: 36, blank: 37.2, say: 37.8, giggle: 40.2, laugh: 41.2, lunch: 44,
  // 5 LUNCH ALONE
  lwalk: 44, pass: 45.4, sit: 47.6, chatPOV: 48.6, ping: 49.0, crushS: 52,
  // 6 THE CRUSH
  approach: 52, wave: 54.4, waveBack: 55.2, reveal: 56.3, drop: 57.2, cafe: 60,
  // 7 YOU TOO
  enjoy: 61.0, youtoo: 62.9, pause: 63.9, speed: 65.4, bell: 67.0, call: 68,
  // 8 MOM CALLS
  ring: 68.4, decline: 71.3, notnow: 71.9, momText: 73.3, home: 76,
  // 9 WALK HOME
  street: 76, doorShut: 81.0, flop: 83.0, night: 85,
  // 10 EYES OPEN
  snap: 86.0, eyesPOV: 88.0, notAgain: 89.4, math: 93,
  // 11 THE MATH
  count: 93.4, jump319: 96.4, sleepEq: 97.4, replay: 101,
  // 12 THE REPLAY BEGINS
  r1: 102, r2: 107, r3: 112, song: 117,
  // 13 JUST ONE SONG
  oneSong: 118.4, play: 121.4, songWide: 122.6, imag: 125,
  // 14 IMAGINATION MODE
  spot: 125, cheer: 127, car: 131, house: 133.5, crush2: 136, real: 138.5, skip: 141, drift: 141.5,
  // 15 THE DRIFT
  hover: 143.5, oneLook: 145, nobody: 147, dark: 149.5, empty: 151, guilty: 152.2, awake: 153.4, pull: 154.4, storm: 156,
  // 16 THE STORM
  feed: 162, f1: 162.6, f2: 163.8, battery: 165.4, why: 166.6, flood: 167.6, dies: 170,
  // 17 PHONE DIES
  dieClick: 170.8, br1: 172.0, br2: 173.6, br3: 175.2, fridge: 176,
  // 18 FRIDGE LIGHT
  toe: 178.2, ow: 178.5, open: 181.2, glass: 182.6, gulp: 183.4, chips: 183.8, list: 187,
  // 19 THE LIST
  today: 187.6, l1: 189.2, l2: 190.2, l3: 191.2, l4: 192.2, bad: 193.8, underline: 195.2, shrink: 196.5, fact2: 197.2, callback: 202,
  // 20 THE CALLBACK
  openChat: 203.4, typeS: 204.2, sent: 208.8, typing: 210.0, split: 211.2, reply: 213.0, awakeToo: 214.6, next: 217,
  // 21 NEXT NIGHT
  tag307: 218.6, remember: 220.2, smirk: 222.0, flip: 223.4, notTonight: 224.8, fade: 226, card: 228,
  // END CARD
  c1: 229, c2: 232.2, c3: 233.8, END: 236,
};
