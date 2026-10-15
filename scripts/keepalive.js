// keepalive.js — paste into a tab via CDP Runtime.evaluate (userGesture:true).
// Silent sound loop: Chrome treats the tab like a music player and does not freeze it in the background.
// From the 2026-10-14 deep-research report (t-mullen/silent-audio pattern). Returns ctx.state ("running" = good).
(() => {
  if (window.__agentKeepAliveActive) return "ALREADY_ACTIVE";
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  const ctx = new AudioCtx();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  gain.gain.value = 0.00001;           // sub-audible, but not zero (zero gets optimized away)
  osc.connect(gain); gain.connect(ctx.destination); osc.start(0);
  if (navigator.wakeLock && navigator.wakeLock.request) navigator.wakeLock.request('screen').catch(() => {});
  document.addEventListener('visibilitychange', () => { if (ctx.state !== 'running') ctx.resume().catch(() => {}); });
  window.__agentKeepAliveActive = { ctx, osc, gain };
  return ctx.state;
})();
