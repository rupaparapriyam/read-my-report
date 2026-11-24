/* Niqo, drawn.
 *
 * One rounded form, two eyes, a small antenna. No gradients, no shine, no cartoon
 * mouth: this sits on a page about someone's blood test, so the character has to be
 * friendly without being jolly. It carries state instead of decoration — resting,
 * reading, thinking, and done — which is also how the page shows what it is doing.
 */
(function (global) {
  const C = {
    body: "#0b4f45", face: "#ffffff", glow: "#eaf3f0",
  };

  function svg(state, size) {
    const blink = state === "rest" ? `
      <animate attributeName="ry" values="3.1;3.1;0.4;3.1;3.1" dur="5.2s"
               keyTimes="0;0.86;0.9;0.94;1" repeatCount="indefinite"/>` : "";
    // Reading: eyes track left to right, like scanning a line.
    const scan = state === "read" ? `
      <animate attributeName="cx" values="20.6;23.4;20.6" dur="1.5s" repeatCount="indefinite"/>` : "";
    const scan2 = state === "read" ? `
      <animate attributeName="cx" values="29.4;32.2;29.4" dur="1.5s" repeatCount="indefinite"/>` : "";
    // Thinking: the antenna pulses.
    const pulse = state === "think" ? `
      <animate attributeName="r" values="2.2;3.4;2.2" dur="1.1s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="1;.45;1" dur="1.1s" repeatCount="indefinite"/>` : "";
    const eyeR = state === "done" ? 0.9 : 3.1;
    const happy = state === "done" ? `
      <path d="M19 27.5q2.4 2.2 4.8 0" stroke="${C.face}" stroke-width="1.8"
            stroke-linecap="round" fill="none"/>
      <path d="M28.2 27.5q2.4 2.2 4.8 0" stroke="${C.face}" stroke-width="1.8"
            stroke-linecap="round" fill="none"/>` : "";
    return `<svg viewBox="0 0 52 52" width="${size}" height="${size}" role="img"
                 aria-label="Niqo" class="niqo-svg niqo-${state}">
      <line x1="26" y1="9" x2="26" y2="13.5" stroke="${C.body}" stroke-width="2.2"
            stroke-linecap="round"/>
      <circle cx="26" cy="7.4" r="2.2" fill="${C.body}">${pulse}</circle>
      <rect x="7" y="13.5" width="38" height="31" rx="12.5" fill="${C.body}"/>
      ${state === "done" ? happy : `
        <ellipse cx="20.6" cy="27.5" rx="3.1" ry="${eyeR}" fill="${C.face}">${blink}${scan}</ellipse>
        <ellipse cx="29.4" cy="27.5" rx="3.1" ry="${eyeR}" fill="${C.face}">${blink}${scan2}</ellipse>`}
      <rect x="18" y="36" width="16" height="2.4" rx="1.2" fill="${C.face}" opacity=".32"/>
    </svg>`;
  }

  global.Niqo = {
    /** Put Niqo into an element, in one of: rest, read, think, done. */
    set(el, state = "rest", size = 44) {
      if (el) el.innerHTML = svg(state, size);
    },
    html: svg,
  };
})(window);
