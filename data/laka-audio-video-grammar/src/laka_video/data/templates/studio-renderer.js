  // LAVC Studio renderer — the design authority for every frame.
  //
  // Rules this file is required to hold to (Ryan Perez / LAKA design system):
  //   * One typeface (Inter), two weights (400 / 600). Drama comes from size and
  //     tracking, never from a third weight or a second family.
  //   * Huge tight headlines against tiny wide micro-labels. That tension IS the
  //     typography.
  //   * One strong left rail. Nothing is centred; emptiness is composed into the
  //     right-hand column and above the statement, never left over underneath it.
  //   * Depth from light, not shadows: a white backlight, 1px hairlines, one
  //     surface tone above the canvas. No drop shadows anywhere.
  //   * Motion is one ease-out curve with a 24px rise and a 90ms stagger.
  //     Nothing bounces, blinks, pulses, spins or snaps.
  //   * Text is fitted, never truncated. A frame that ends in "…" is a bug.
  //   * A frame never repeats itself: a headline that restates the figure it sits
  //     above is suppressed rather than shown twice.
  //
  // The frame chrome (canvas, backlight, grain, camera drift, caption band) is
  // owned by renderAt in player.html.j2. This file returns scene content only,
  // positioned in the raw W x H design space.

  // ---------------------------------------------------------------- easing ---
  // The design system's single curve: cubic-bezier(0.16, 1, 0.3, 1).
  function dsEase(x) {
    x = clamp(x);
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    const cx = 3 * 0.16, bx = 3 * (0.3 - 0.16) - cx, ax = 1 - cx - bx;
    const cy = 3 * 1.0, by = 3 * (1.0 - 1.0) - cy, ay = 1 - cy - by;
    const fx = u => ((ax * u + bx) * u + cx) * u;
    const dfx = u => (3 * ax * u + 2 * bx) * u + cx;
    let u = x;
    for (let i = 0; i < 6; i++) {
      const err = fx(u) - x;
      if (Math.abs(err) < 1e-6) break;
      const slope = dfx(u);
      if (Math.abs(slope) < 1e-6) break;
      u -= err / slope;
    }
    u = clamp(u);
    return ((ay * u + by) * u + cy) * u;
  }

  // -------------------------------------------------------------- measuring ---
  const MEASURE = document.createElement("canvas").getContext("2d");
  const FALLBACK_STACK = "system-ui, -apple-system, 'Segoe UI', sans-serif";

  function measureFont(size, weight, tracking) {
    MEASURE.font = `${weight} ${size}px 'Inter', ${FALLBACK_STACK}`;
    if ("letterSpacing" in MEASURE) MEASURE.letterSpacing = `${tracking * size}px`;
  }

  // The widest line the wrap produced. Counting lines is not enough: a single
  // unbreakable word ("accessibility-first") can be wider than the box on its
  // own, and no amount of wrapping will help — only shrinking will.
  function widestLine(lines, size, weight, tracking) {
    measureFont(size, weight, tracking);
    let widest = 0;
    for (const line of lines) widest = Math.max(widest, MEASURE.measureText(line).width);
    return widest;
  }

  function wrapLines(text, boxWidth, size, weight, tracking) {
    const source = String(text || "").trim();
    if (!source) return [];
    measureFont(size, weight, tracking);
    const tokens = source.split(/\s+/);
    const out = [];
    let current = "";
    for (const token of tokens) {
      const candidate = current ? `${current} ${token}` : token;
      if (current && MEASURE.measureText(candidate).width > boxWidth) {
        out.push(current);
        current = token;
      } else {
        current = candidate;
      }
    }
    if (current) out.push(current);
    return out;
  }

  // Fit text by stepping the size down. NOTHING IS EVER CUT. A line that has to
  // shrink is honest; a line that ends in "…" is not, and a line that spills out
  // of its box is worse than either. The legibility floor is the preferred
  // stopping point, but when a sentence still will not fit at the floor the type
  // keeps shrinking to an absolute minimum rather than overflowing — and the
  // result reports that it went under, so the linter can say so.
  const ABSOLUTE_MIN_UNITS = 1.7;

  function fitText(text, boxWidth, boxHeight, options) {
    const opt = Object.assign({ max: 12, min: 4.4, weight: 600, tracking: -0.05, leading: 1.02, maxLines: 6 }, options || {});
    const source = String(text || "").trim();
    if (!source) return { lines: [], size: opt.min * U, leading: opt.leading, height: 0 };
    for (let step = 0; step <= 44; step++) {
      const size = (opt.max - (opt.max - opt.min) * (step / 44)) * U;
      const lines = wrapLines(source, boxWidth, size, opt.weight, opt.tracking);
      const height = lines.length * size * opt.leading;
      const fitsWidth = widestLine(lines, size, opt.weight, opt.tracking) <= boxWidth + 1;
      if (lines.length <= opt.maxLines && height <= boxHeight && fitsWidth) {
        return { lines, size, leading: opt.leading, height };
      }
    }
    // Below the preferred floor: keep going rather than let it overflow.
    for (let step = 1; step <= 20; step++) {
      const size = (opt.min - (opt.min - ABSOLUTE_MIN_UNITS) * (step / 20)) * U;
      const lines = wrapLines(source, boxWidth, size, opt.weight, opt.tracking);
      const fitsWidth = widestLine(lines, size, opt.weight, opt.tracking) <= boxWidth + 1;
      if (lines.length * size * opt.leading <= boxHeight && fitsWidth) {
        return { lines, size, leading: opt.leading, height: lines.length * size * opt.leading,
                 belowFloor: true };
      }
    }
    const size = ABSOLUTE_MIN_UNITS * U;
    const lines = wrapLines(source, boxWidth, size, opt.weight, opt.tracking);
    return { lines, size, leading: opt.leading, height: lines.length * size * opt.leading,
             belowFloor: true };
  }

  // Fit a set of strings at one shared size, so a list reads as one list rather
  // than as several unrelated labels that happened to land near each other.
  function fitTogether(values, boxWidth, boxHeight, options) {
    const opt = Object.assign({ max: 4.4, min: BODY_FLOOR, weight: 600, tracking: -0.03, leading: 1.18, maxLines: 2 }, options || {});
    for (let step = 0; step <= 44; step++) {
      const size = (opt.max - (opt.max - opt.min) * (step / 44)) * U;
      const wrapped = values.map(value => wrapLines(value, boxWidth, size, opt.weight, opt.tracking));
      const tallest = Math.max(0, ...wrapped.map(lines => lines.length));
      const widest = Math.max(0, ...wrapped.map(lines => widestLine(lines, size, opt.weight, opt.tracking)));
      if (tallest <= opt.maxLines && tallest * size * opt.leading <= boxHeight && widest <= boxWidth + 1) {
        return { wrapped, size, leading: opt.leading, lineHeight: size * opt.leading };
      }
    }
    for (let step = 1; step <= 20; step++) {
      const size = (opt.min - (opt.min - ABSOLUTE_MIN_UNITS) * (step / 20)) * U;
      const wrapped = values.map(value => wrapLines(value, boxWidth, size, opt.weight, opt.tracking));
      const tallest = Math.max(0, ...wrapped.map(lines => lines.length));
      const widest = Math.max(0, ...wrapped.map(lines => widestLine(lines, size, opt.weight, opt.tracking)));
      if (tallest * size * opt.leading <= boxHeight && widest <= boxWidth + 1) {
        return { wrapped, size, leading: opt.leading, lineHeight: size * opt.leading, belowFloor: true };
      }
    }
    const size = ABSOLUTE_MIN_UNITS * U;
    const wrapped = values.map(value => wrapLines(value, boxWidth, size, opt.weight, opt.tracking));
    return { wrapped, size, leading: opt.leading, lineHeight: size * opt.leading, belowFloor: true };
  }

  // ------------------------------------------------------------ composition ---
  // Published floors, from perception.yml. Body text below ~2.6% of the short
  // edge stops being readable at social viewing distance, so the fitter clamps
  // here and reduces CONTENT instead of dropping under it.
  const PERCEPTION = STORY.perception || {};
  const TYPO = PERCEPTION.typography || {};
  const BODY_FLOOR = Number(TYPO.body_min_units || 2.8);
  const MICRO_FLOOR = Number(TYPO.micro_min_units || 1.6);
  const MOTION_CFG = PERCEPTION.motion || {};
  const STAGGER_BAND = MOTION_CFG.stagger_ms || [60, 120];
  const STAGGER_BUDGET = Number(MOTION_CFG.stagger_total_budget_ms || 1200);

  const MICRO_SIZE = 2.6 * U;
  const HEAD_GAP = 1.6 * U;
  const BAND_GAP = 3.4 * U;

  // Every scene composes into the same safe area so cuts never jump.
  function frameBox() {
    const reserve = (STORY.captions && C.captions !== "none")
      ? captionReserve + 2.4 * U   // exactly where the caption flood begins
      : 4 * U;
    const top = H * 0.085;
    const bottom = H - reserve;
    return {
      left: edge,
      width: W - edge * 2,
      top, bottom,
      height: bottom - top,
      // The rail the type sits on. The rest of the width is the column the
      // design system leaves deliberately empty.
      rail: (W - edge * 2) * (landscape ? 0.62 : 0.94),
    };
  }

  // Vendler's aspectual class decides HOW a scene enters, because the class is
  // a fact about the claim's temporal shape:
  //
  //   achievement   punctual        -> cut, no travel (below the 100ms floor
  //                                   nothing is communicated by motion anyway)
  //   accomplishment duration+end   -> build and settle
  //   activity       no terminus    -> enters, then never fully comes to rest
  //   state          no change      -> fades, does not move
  //
  // "Sales jumped" is an achievement: the value snaps rather than sliding up.
  function sceneOperator(scene) {
    return String(scene.semantics?.motion_operator || "build_settle");
  }

  // WCAG 2.3.3 / nd-ux: keep the duration, drop the travel. The reveal still
  // times exactly as it does in the standard cut, so the two versions stay in
  // step; only the movement is gone.
  const REDUCED_MOTION = Boolean(C.reduced_motion);

  function revealStyle(p, scene, delayMs, riseUnits, value) {
    // An element carried over from the previous scene is already there.
    if (value !== undefined && isHeld(scene, value)) return heldStyle(p, scene);
    const duration = Math.max(0.001, scene.end - scene.start);
    const operator = sceneOperator(scene);
    const start = (delayMs / 1000) / duration;
    const exit = 1 - dsEase((p - 0.94) / 0.06);

    if (operator === "cut") {
      // 80ms: inside the instantaneous band, so it reads as a state change
      // rather than as a movement.
      const q = clamp((p - start) / Math.max(0.0001, 0.08 / duration));
      return `opacity:${(q * exit).toFixed(4)};`;
    }

    const span = 0.6 / duration;                       // --duration-base: 600ms
    const q = dsEase((p - start) / Math.max(0.0001, span));

    if (operator === "static" || REDUCED_MOTION) {
      // A state does not travel, and neither does anything in a reduced cut.
      return `opacity:${(q * exit).toFixed(4)};`;
    }

    const rise = (riseUnits === undefined ? 2.4 : riseUnits) * U;   // --rise: 24px
    let offset = (1 - q) * rise;
    if (operator === "loop") {
      // An activity has no terminus, so it never fully settles. The residual
      // drift is small enough to stay under the vestibular threshold and large
      // enough to read as "still going".
      const t = (p * duration);
      offset += q * 0.22 * U * Math.sin(t * 1.6 + (delayMs / 260));
    }
    return `opacity:${(q * exit).toFixed(4)};transform:translateY(${px(offset)});`;
  }

  // -------------------------------------------------------------- carrier ---
  // A scene that continues an object already on screen must not rebuild it.
  // Re-entering a rail, a panel outline or an unchanged eyebrow tells the
  // viewer "new thing" when the truth is "same thing, more of it", and that is
  // the difference between one argument and a stack of slides.
  const SCENE_BY_ID = new Map((STORY.scenes || []).map(s => [s.id, s]));

  function carrierOf(scene) {
    return scene.carrier || null;
  }

  function previousScene(scene) {
    const carrier = carrierOf(scene);
    return carrier ? SCENE_BY_ID.get(carrier.from) || null : null;
  }

  // Held: already present, so it neither fades nor travels. It only exits.
  function heldStyle(p, scene) {
    const exit = 1 - dsEase((p - 0.94) / 0.06);
    return `opacity:${exit.toFixed(4)};`;
  }

  // True when this exact string was on screen in the scene before.
  function isHeld(scene, value) {
    const carrier = carrierOf(scene);
    if (!carrier || !value) return false;
    const norm = textNorm(value);
    if (!norm) return false;
    if ((carrier.shared || []).some(entity => norm.includes(textNorm(entity)))) return true;
    const before = previousScene(scene);
    if (!before) return false;
    const payload = before.payload || {};
    return ["headline", "label", "left", "right", "center", "parent", "term"]
      .some(key => payload[key] && textNorm(payload[key]) === norm);
  }

  // Structural chrome holds whenever the geometry itself is continuing.
  function frameHolds(scene) {
    const carrier = carrierOf(scene);
    return Boolean(carrier && (carrier.mode === "frame" || carrier.mode === "persist"));
  }

  // ------------------------------------------------------------- modality ---
  // Grammatical certainty must survive into the frame, or the graphic asserts
  // more than the speaker did. A hedged claim drawn solid is a lie-factor
  // violation in the labelling channel rather than the geometric one.
  function modalityOf(scene) {
    const sem = scene.semantics || {};
    return {
      level: String(sem.modality || "asserted"),
      stroke: String(sem.modality_render?.stroke || (sem.modality === "possible" || sem.modality === "forecast" ? "dashed" : "solid")),
      opacity: sem.modality === "possible" ? 0.78 : sem.modality === "forecast" ? 0.86 : 1,
      approximate: sem.modality === "approximate" || sem.label_precision === "rounded",
      attributed: sem.modality === "attributed",
    };
  }

  // A surface carries its own certainty: dashed means "stated as possible".
  function certaintyBorder(scene, colour) {
    const mode = modalityOf(scene);
    return `border:1px ${mode.stroke === "dashed" ? "dashed" : "solid"} ${colour};`;
  }

  // §8: negation is a two-step comprehension process. Show the object, THEN
  // strike it. An empty frame does not communicate "no sales" — it communicates
  // nothing, and the negated content stays partially activated either way.
  // A strike is only drawn over an object the frame separately shows — a pair
  // panel, a figure — never across a free headline. Without a parser there is
  // no way to know which span the negation scopes over, and striking the whole
  // line for a phrase-level negation states the opposite of the sentence.
  // Congruent beats none beats incongruent: when the target is unknown, the
  // negation is recorded in the storyboard and left undrawn.
  // Predicate negation, in the words that actually carry it.
  const NEGATION_MARKER = /\b(?:not|never|no longer|cannot|can't|won't|didn't|doesn't|isn't|aren't|don't)\b/i;

  function carriesNegation(scene, value, side) {
    if (!scene.semantics?.negation) return false;
    // The marker usually survives in the span, but pair extraction strips it:
    // "We did not rebuild it by hand" becomes the panel "Rebuild it by hand".
    // In a "not X, but Y" contrast the left panel IS X, which is the half being
    // rejected, so the structure identifies the target when the words no longer
    // do. Anything else needs the marker present, because guessing which half a
    // negation lands on would state the opposite of the sentence.
    if (NEGATION_MARKER.test(String(value || ""))) return true;
    const contrast = String(scene.event?.direction || "") === "indirect_opposite";
    return contrast && side === "left";
  }

  function strikeThrough(scene, p, target) {
    const negation = scene.semantics?.negation;
    if (!negation || !target) return "";
    const draw = revealAmount(p, scene, 620, 420);
    if (draw <= 0.001) return "";
    // The object is shown first and struck after — the two-step the reader
    // performs anyway. Striking from nothing communicates nothing.
    return `<div style="position:absolute;left:0;right:0;top:50%;height:${px(.3 * U)};background:${colors.danger};transform-origin:0 50%;transform:scaleX(${draw.toFixed(4)});"></div>`;
  }

  // Gestalt common fate: 60-120ms reads as ONE group building, and the total
  // build has to stay inside the budget, so the step shrinks as the list grows.
  function staggerFor(count) {
    const [low, high] = STAGGER_BAND;
    return clamp(STAGGER_BUDGET / Math.max(1, count), Number(low), Number(high));
  }

  function revealAmount(p, scene, delayMs, durationMs) {
    const duration = Math.max(0.001, scene.end - scene.start);
    const start = (delayMs / 1000) / duration;
    const span = ((durationMs === undefined ? 600 : durationMs) / 1000) / duration;
    return dsEase((p - start) / Math.max(0.0001, span));
  }

  // Micro-label: tiny and wide, the counterweight to the headline. A label that
  // restates the headline is not a counterweight, it is the same weight twice.
  function microLabel(text, p, scene, delayMs, color, against) {
    if (!text) return "";
    if (against && echoes(text, against)) return "";
    return `<div style="${revealStyle(p, scene, delayMs === undefined ? 0 : delayMs, 1.2, text)}font:600 ${px(MICRO_SIZE)}/1 ${font};letter-spacing:.12em;text-transform:uppercase;color:${color || colors.muted};">${esc(String(text).toUpperCase())}</div>`;
  }

  // Headlines reveal line by line, like a shot list — never word by word.
  function headlineLines(fitted, p, scene, options) {
    const opt = Object.assign({ color: colors.text, delay: 90 }, options || {});
    if (!fitted.lines.length) return "";
    if (opt.stagger === undefined) opt.stagger = staggerFor(fitted.lines.length);
    const rendered = fitted.lines.map((line, index) =>
      `<div style="${revealStyle(p, scene, opt.delay + index * opt.stagger, undefined, line)}font:600 ${px(fitted.size)}/${fitted.leading} ${font};letter-spacing:-.05em;color:${opt.color};white-space:pre;">${esc(line)}</div>`
    ).join("");
    return `<div style="display:flex;flex-direction:column;">${rendered}</div>`;
  }

  function headlineBlock(text, p, scene, box, options) {
    const opt = Object.assign({ max: 12.4, min: 5.2, maxLines: 5 }, options || {});
    const fitted = fitText(text, box.width, box.height, {
      max: opt.max, min: opt.min, weight: 600, tracking: -0.05, leading: 1.02, maxLines: opt.maxLines,
    });
    return headlineLines(fitted, p, scene, opt);
  }

  function bodyText(text, p, scene, box, delayMs, color) {
    if (!text) return "";
    const fitted = fitText(text, box.width, box.height, {
      max: 3.8, min: BODY_FLOOR, weight: 400, tracking: -0.012, leading: 1.5, maxLines: 5,
    });
    if (!fitted.lines.length) return "";
    return `<div style="${revealStyle(p, scene, delayMs === undefined ? 420 : delayMs)}font:400 ${px(fitted.size)}/${fitted.leading} ${font};letter-spacing:-.012em;color:${color || colors.body};max-width:${px(box.width)};">${esc(fitted.lines.join(" "))}</div>`;
  }

  // A statement frame: the micro-label holds the top of the safe area, the
  // statement is seated on the lower third. The air between them is the
  // composition — it is not space the layout failed to fill.
  function statementFrame(eyebrow, block, scene, p) {
    const box = frameBox();
    const mode = scene ? modalityOf(scene) : { opacity: 1 };
    // Statement frames show one free line; there is no separately-drawn object
    // for a strike to land on, so none is drawn here.
    const strike = "";
    return `<div style="position:absolute;left:${px(box.left)};top:${px(box.top)};width:${px(box.rail)};height:${px(box.height)};opacity:${mode.opacity};">
      <div style="position:absolute;left:0;top:0;">${eyebrow}</div>
      <div style="position:absolute;left:0;bottom:0;width:100%;display:flex;flex-direction:column;align-items:flex-start;gap:${px(2.4 * U)};">
        <div style="position:relative;width:100%;">${block}${strike}</div>
      </div>
    </div>`;
  }

  // A structured frame: micro-label and headline hold the top, the figure gets
  // an exactly measured band underneath. Nothing is guessed, so no dead strip
  // opens up at the bottom of the frame.
  function structuredFrame(head, figureFor) {
    const box = frameBox();
    const bandTop = box.top + head.height + BAND_GAP;
    const bandHeight = Math.max(8 * U, box.bottom - bandTop);
    // A figure under a headline is seated on the bottom of the band, so the air
    // collects between the two. A figure with no headline above it has no reason
    // to hug the caption band, so it takes the whole band instead.
    const band = { left: box.left, top: bandTop, width: box.width, height: bandHeight, hasHead: Boolean(head.hasHeadline) };
    return `<div style="position:absolute;left:${px(box.left)};top:${px(box.top)};width:${px(box.rail)};display:flex;flex-direction:column;gap:${px(HEAD_GAP)};">${head.html}</div>
      <div style="position:absolute;left:${px(band.left)};top:${px(band.top)};width:${px(band.width)};height:${px(band.height)};">${figureFor(band)}</div>`;
  }

  // Builds the head block and reports exactly how tall it is.
  function buildHead(scene, p, label, headline, options) {
    const box = frameBox();
    const opt = Object.assign({ max: 8.6, min: 4.2, maxLines: 3 }, options || {});
    const fitted = fitText(headline, box.rail, box.height * 0.34, {
      max: opt.max, min: opt.min, weight: 600, tracking: -0.05, leading: 1.02, maxLines: opt.maxLines,
    });
    const hasLabel = Boolean(label);
    const height = (hasLabel ? MICRO_SIZE : 0) + (hasLabel && fitted.height ? HEAD_GAP : 0) + fitted.height;
    return {
      html: microLabel(label, p, scene, 0, undefined, headline) + headlineLines(fitted, p, scene, {}),
      height,
      // A lone micro-label is not a head to hang a figure under: without a
      // headline above it the figure takes the whole band.
      hasHeadline: fitted.lines.length > 0,
    };
  }

  // A frame that says the same thing twice is noise. Two strings echo each other
  // when they are equal, or when the longer simply contains the shorter and the
  // shorter is substantial enough for the repeat to be visible.
  const textNorm = value => String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();

  function echoes(a, b) {
    const left = textNorm(a), right = textNorm(b);
    if (!left || !right) return false;
    if (left === right) return true;
    const [shortText, longText] = left.length <= right.length ? [left, right] : [right, left];
    return shortText.split(" ").length >= 4 && longText.includes(shortText);
  }

  function dropEchoes(value, others) {
    for (const other of others) {
      if (echoes(value, other)) return "";
    }
    return value;
  }

  const headlineUnlessEcho = dropEchoes;

  // ------------------------------------------------------------------ rows ---
  // The design system's List: an accent arrow or a zero-padded accent numeral,
  // separated by hairlines. Never a bullet, never a card with a hollow interior.
  function rowStack(values, p, scene, ordered, band) {
    const items = arr(values).filter(Boolean).slice(0, 6);
    if (!items.length) return "";
    const glyphWidth = 5.4 * U;
    const rowPad = 1.6 * U;
    const textWidth = band.width - glyphWidth;
    const perRow = band.height / items.length;
    // A short list gets big type rather than the same small type floating in a
    // tall band. Type scale carries the emphasis; the air stays above the list,
    // under the headline, where the design system wants it.
    const rowMax = items.length <= 2 ? 7.2 : items.length <= 4 ? 5.8 : 4.6;
    // A short list can afford a third line. Forcing two lines on a long row just
    // shrinks the whole list to fit the one item that did not want to wrap.
    const rowLines = items.length <= 3 ? 3 : 2;
    const fit = fitTogether(items, textWidth, perRow - rowPad * 2, { max: rowMax, min: BODY_FLOOR, maxLines: rowLines });
    const rowStep = staggerFor(items.length);
    const rows = items.map((value, index) => {
      const step = rowStep;
      const style = revealStyle(p, scene, 260 + index * step);
      const glyph = ordered
        ? `<span style="font:600 ${px(fit.size * 0.82)}/1 ${font};letter-spacing:-.02em;color:${colors.accent};font-variant-numeric:tabular-nums;">${String(index + 1).padStart(2, "0")}</span>`
        : `<span style="font:600 ${px(fit.size * 0.9)}/1 ${font};color:${colors.accent};">&#8594;</span>`;
      const holdRule = frameHolds(scene);
      return `<div style="${holdRule ? heldStyle(p, scene) : style}display:flex;align-items:baseline;gap:${px(2.4 * U)};padding:${px(rowPad)} 0;border-top:1px solid ${index === 0 ? "transparent" : colors.hairSoft};">
        <div style="flex:0 0 ${px(glyphWidth - 2.4 * U)};">${glyph}</div>
        <div style="flex:1 1 auto;font:600 ${px(fit.size)}/${fit.leading} ${font};letter-spacing:-.03em;color:${colors.text};">${esc(fit.wrapped[index].join(" "))}</div></div>`;
    }).join("");
    // Seated on the bottom of the band: the air lands between the headline and
    // the list, where it reads as air.
    const seat = band.hasHead ? "bottom:0;" : "top:0;bottom:0;justify-content:center;";
    return `<div style="position:absolute;left:0;right:0;${seat}display:flex;flex-direction:column;">${rows}</div>`;
  }

  // ------------------------------------------------------------ image slide ---
  // The design system's own treatment: one grade over the photograph, a
  // gradient flood protecting the type rather than a solid capsule behind it,
  // and a cinema crop rather than a photo ratio.
  function imageSlide(scene, p) {
    const P = scene.payload || {};
    const box = frameBox();
    const asset = P.asset || scene.asset;
    const drift = REDUCED_MOTION ? 1 : 1.08 - 0.045 * dsEase(p);
    const media = asset
      ? `<div style="position:absolute;inset:0;overflow:hidden;">
           <img src="${esc(asset)}" alt="" style="width:100%;height:100%;object-fit:cover;transform:scale(${drift.toFixed(4)});filter:saturate(.85) contrast(.92);" /></div>
         <div style="position:absolute;inset:0;background:linear-gradient(90deg,rgba(7,9,13,.94) 0%,rgba(7,9,13,.78) 38%,rgba(7,9,13,.12) 72%,transparent 100%);"></div>
         <div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,rgba(7,9,13,.35) 70%,rgba(7,9,13,.85) 100%);"></div>`
      : "";
    return media + statementFrame(
      microLabel(P.label || STORY.content?.speaker || "", p, scene, 0, undefined, P.headline),
      headlineBlock(P.headline || scene.text, p, scene,
                    { width: box.rail, height: box.height * 0.58 }, { max: 12.4, min: 5.4, maxLines: 5 }) +
      bodyText(headlineUnlessEcho(P.supporting, [P.headline]), p, scene,
               { width: box.rail, height: box.height * 0.14 }, 480),
      scene, p
    );
  }

  // ----------------------------------------------------------------- matrix ---
  // Position along two scales is the most accurate quantitative channel there
  // is (Cleveland & McGill ranks 1 and 2), so the axes carry the meaning and
  // every point is directly labelled — no legend, no colour key.
  function matrixFigure(scene, p) {
    const P = scene.payload || {};
    const points = arr(P.points).slice(0, 12);
    const xAxis = arr(P.x_axis);
    const yAxis = arr(P.y_axis);
    const head = buildHead(scene, p, P.label || "Matrix", P.headline || scene.text,
                           { max: 7.6, min: 4.2, maxLines: 2 });
    const grid = revealAmount(p, scene, 120, 700);
    return structuredFrame(head, band => {
      const pad = 6 * U;
      const left = pad, right = band.width - 2 * U;
      const top = 2 * U, bottom = band.height - pad;
      const width = Math.max(1, right - left), height = Math.max(1, bottom - top);
      const axes = `
        <div style="position:absolute;left:${px(left)};top:${px(top)};width:${px(width)};height:${px(height)};
             border-left:1px solid ${colors.hair};border-bottom:1px solid ${colors.hair};
             transform:scaleY(${grid.toFixed(3)});transform-origin:0 100%;"></div>
        <div style="position:absolute;left:${px(left)};top:${px(top + height / 2)};width:${px(width * grid)};height:1px;background:${colors.hairSoft};"></div>
        <div style="position:absolute;left:${px(left + width / 2)};top:${px(top)};width:1px;height:${px(height * grid)};background:${colors.hairSoft};"></div>`;
      const label = (text, style) =>
        `<div style="position:absolute;${style}font:600 ${px(MICRO_SIZE)}/1 ${font};letter-spacing:.12em;text-transform:uppercase;color:${colors.muted};">${esc(String(text).toUpperCase())}</div>`;
      const axisLabels =
        (xAxis[0] ? label(xAxis[0], `left:${px(left)};top:${px(bottom + 1.6 * U)};`) : "") +
        (xAxis[1] ? label(xAxis[1], `right:0;top:${px(bottom + 1.6 * U)};`) : "") +
        (yAxis[1] ? label(yAxis[1], `left:${px(left)};top:${px(top - 2.2 * U)};`) : "") +
        (yAxis[0] ? label(yAxis[0], `left:${px(left)};top:${px(bottom - 3.4 * U)};`) : "");
      const plateW = Math.min(band.width * 0.34, 20 * U);
      const fit = fitTogether(points.map(pt => String(pt.label || "")), plateW, 6 * U,
                              { max: 2.9, min: BODY_FLOOR, weight: 600, tracking: -0.02, leading: 1.15, maxLines: 2 });
      const dots = points.map((point, index) => {
        const q = revealAmount(p, scene, 320 + index * staggerFor(points.length), 600);
        const x = left + clamp(Number(point.x)) * width;
        const y = bottom - clamp(Number(point.y)) * height;
        const rightHalf = x > left + width * 0.62;
        return `<div style="position:absolute;left:${px(x - 1.1 * U)};top:${px(y - 1.1 * U)};width:${px(2.2 * U)};height:${px(2.2 * U)};border-radius:50%;background:${colors.accent};opacity:${q.toFixed(3)};"></div>
          <div style="position:absolute;${rightHalf ? `right:${px(band.width - x + 2 * U)};text-align:right;` : `left:${px(x + 2 * U)};`}top:${px(y - 1.6 * U)};width:${px(plateW)};opacity:${q.toFixed(3)};font:600 ${px(fit.size)}/${fit.leading} ${font};letter-spacing:-.02em;color:${colors.text};">${esc(fit.wrapped[index].join(" "))}</div>`;
      }).join("");
      return `${axes}${axisLabels}${dots}`;
    });
  }

  // ------------------------------------------------------ library elements ---
  // The Studio element library draws anything the grammar marks with `element`.
  // It is the author's own registry — 52 elements against the 23 this renderer
  // implements — shipped conformed to the design system so its motion matches
  // everything else in the frame rather than reintroducing overshoot.
  const LIBRARY = new Map(((window.LAVC_ELEMENTS) || []).map(e => [e.id, e]));

  function libraryContext() {
    return {
      // The library predates the token cleanup and asks for `accent2`, which
      // is not a design-system colour. Binding it to accent-hover here resolves
      // it at the boundary rather than by rewriting the library's source.
      c: Object.assign({}, colors, { accent2: colors.accentHover }),
      wash: "", W, H, U,
      F: font,
      px: n => `${Math.round(n * 100) / 100}px`,
    };
  }

  function renderLibraryElement(scene, p, t) {
    const element = LIBRARY.get(String(scene.element || ""));
    if (!element || typeof element.render !== "function") return null;
    try {
      return element.render(p, t, libraryContext(), scene.payload || {});
    } catch (error) {
      // A broken element must not take the film down: fall back to the
      // congruent-typography default, which is the safe move anyway.
      if (DEBUG) console.error("element", scene.element, error);
      return null;
    }
  }

  // -------------------------------------------------------------- templates ---
  function renderStudioTemplate(scene, p, t) {
    if (scene.element) {
      const drawn = renderLibraryElement(scene, p, t);
      if (drawn !== null) return drawn;
    }
    if (scene.layout === "image_overlay") return imageSlide(scene, p);
    if (scene.template === "matrix") return matrixFigure(scene, p);

    const P = scene.payload || {};
    const box = frameBox();
    const items = arr(P.items || P.nodes || P.children);
    const template = scene.template;
    const speaker = STORY.content?.speaker || "";

    // ---- statement family ---------------------------------------------------
    if (template === "title_card" || template === "quote_focus") {
      const quote = template === "quote_focus";
      const eyebrow = quote
        ? `<div style="${revealStyle(p, scene, 0, 1.2)}font:600 ${px(7 * U)}/.62 ${font};color:${colors.accent};">&#8220;</div>`
        : microLabel(P.label || speaker, p, scene, 0, undefined, P.headline);
      const supporting = headlineUnlessEcho(P.supporting, [P.headline]);
      return statementFrame(eyebrow,
        headlineBlock(P.headline || scene.text, p, scene, { width: box.rail, height: box.height * 0.66 }, { max: 12.4, min: 5.4, maxLines: 5 }) +
        bodyText(supporting, p, scene, { width: box.rail, height: box.height * 0.16 }, 480),
        scene, p
      );
    }

    if (template === "question_card") {
      return statementFrame(microLabel(P.label || "The question", p, scene, 0, undefined, P.headline),
        headlineBlock(P.headline || scene.text, p, scene, { width: box.rail, height: box.height * 0.66 }, { max: 11.6, min: 5.2, maxLines: 5 }) +
        `<div style="${revealStyle(p, scene, 520, 1.2)}width:${px(6 * U)};height:${px(.34 * U)};background:${colors.accent};"></div>`
      );
    }

    if (template === "definition_card") {
      const line = revealAmount(p, scene, 380, 900);
      return statementFrame(microLabel(P.label || "Definition", p, scene, 0),
        headlineBlock(P.term || P.headline, p, scene, { width: box.rail, height: box.height * 0.44 }, { max: 12, min: 5.4, maxLines: 3 }) +
        `<div style="height:${px(.34 * U)};width:${pct(line * 0.44)};background:${colors.accent};"></div>` +
        bodyText(P.definition || P.supporting, p, scene, { width: box.rail, height: box.height * 0.24 }, 560)
      );
    }

    if (template === "warning_card") {
      const eyebrow = `<div style="${revealStyle(p, scene, 0, 1.2)}display:flex;align-items:center;gap:${px(1.8 * U)};">
           <span style="width:${px(4 * U)};height:${px(4 * U)};border-radius:50%;border:${px(.26 * U)} solid ${colors.danger};display:grid;place-items:center;font:600 ${px(2.6 * U)}/1 ${font};color:${colors.danger};">!</span>
           <span style="font:600 ${px(MICRO_SIZE)}/1 ${font};letter-spacing:.12em;text-transform:uppercase;color:${colors.danger};">${esc(String(P.label || "Important").toUpperCase())}</span>
         </div>`;
      return statementFrame(eyebrow,
        headlineBlock(P.headline || scene.text, p, scene, { width: box.rail, height: box.height * 0.58 }, { max: 11, min: 5.2, maxLines: 5 }) +
        bodyText(headlineUnlessEcho(P.supporting, [P.headline]), p, scene, { width: box.rail, height: box.height * 0.16 }, 520)
      );
    }

    // The blue full-bleed CTA is the one saturated scene change in the film.
    if (template === "cta_card") {
      // The composition pass decides which single scene spends the accent; a
      // second saturated frame would halve the salience of both.
      if (scene.accent_bleed === false) {
        return statementFrame(
          microLabel(P.label || "", p, scene, 0, undefined, P.headline),
          headlineBlock(P.headline || scene.text, p, scene, { width: box.rail, height: box.height * 0.62 }, { max: 12.4, min: 5.4, maxLines: 5 }) +
          (P.destination ? `<div style="${revealStyle(p, scene, 620, 1.2)}font:600 ${px(MICRO_SIZE)}/1 ${font};letter-spacing:.12em;text-transform:uppercase;color:${colors.accentHover};">${esc(String(P.destination).toUpperCase())}</div>` : ""),
          scene, p
        );
      }
      const sweep = revealAmount(p, scene, 0, 700);
      const button = revealAmount(p, scene, 700, 600);
      const onAccent = colors.onAccent;
      const action = P.action
        ? `<div style="opacity:${button.toFixed(4)};transform:translateY(${px((1 - button) * 2.4 * U)});display:inline-flex;align-items:center;gap:${px(1.4 * U)};padding:${px(2.2 * U)} ${px(4 * U)};border-radius:999px;background:${onAccent};font:600 ${px(3 * U)}/1 ${font};letter-spacing:-.01em;color:${colors.accentPress};">${esc(P.action)}<span>&#8594;</span></div>`
        : "";
      const destination = P.destination
        ? `<div style="${revealStyle(p, scene, 900, 1.2)}font:600 ${px(MICRO_SIZE)}/1 ${font};letter-spacing:.12em;text-transform:uppercase;color:rgba(245,247,250,.78);">${esc(String(P.destination).toUpperCase())}</div>`
        : "";
      return `<div style="position:absolute;inset:0;background:${colors.accent};transform:scaleY(${sweep.toFixed(4)});transform-origin:50% 100%;"></div>` +
        statementFrame(
          microLabel(P.label || "", p, scene, 200, "rgba(245,247,250,.72)", P.headline),
          headlineBlock(P.headline || scene.text, p, scene, { width: box.rail, height: box.height * 0.52 }, { max: 12.4, min: 5.4, maxLines: 4, delay: 300, color: onAccent }) +
          bodyText(headlineUnlessEcho(P.supporting, [P.headline]), p, scene, { width: box.rail, height: box.height * 0.14 }, 600, "rgba(245,247,250,.86)") +
          action + destination
        );
    }

    // The number is the proof. It is revealed at its exact value and never
    // animates through wrong figures on its way there.
    if (template === "big_number") {
      const value = String(P.number || "");
      const reveal = revealAmount(p, scene, 120, 700);
      const fitted = fitText(value, box.rail, box.height * 0.5, { max: 30, min: 10, weight: 600, tracking: -0.075, leading: 0.86, maxLines: 1 });
      const underline = revealAmount(p, scene, 520, 900);
      return statementFrame(microLabel(P.unit || "Measured", p, scene, 0),
        `<div style="opacity:${reveal.toFixed(4)};transform:translateY(${px((1 - reveal) * 3 * U)});font:600 ${px(fitted.size)}/.86 ${font};letter-spacing:-.075em;color:${colors.text};font-variant-numeric:tabular-nums;">${esc(value)}</div>` +
        `<div style="height:${px(.34 * U)};width:${pct(underline * 0.3)};background:${colors.accent};"></div>` +
        bodyText(P.label, p, scene, { width: box.rail, height: box.height * 0.2 }, 620)
      );
    }

    // ---- row family ---------------------------------------------------------
    if (["list_stack", "steps", "timeline", "funnel", "condition_cards"].includes(template)) {
      const ordered = template !== "list_stack";
      let values = items;
      if (template === "timeline" && arr(P.events).length) {
        values = arr(P.events).map(event => (typeof event === "object" ? event.event : event));
      }
      if (template === "condition_cards" && P.left && P.right && !values.length) {
        values = [P.left, P.right];
      }
      values = values.map(value => (typeof value === "object" ? (value.event || value.label || "") : String(value))).filter(Boolean);
      const label = P.label || { list_stack: "Key points", steps: "Process", timeline: "Timeline", funnel: "Stages", condition_cards: "If / then" }[template];
      const headline = headlineUnlessEcho(P.headline || scene.text, values);
      const head = buildHead(scene, p, label, headline);
      return structuredFrame(head, band => rowStack(values, p, scene, ordered, band));
    }

    // ---- pair family --------------------------------------------------------
    if (["before_after", "comparison_split", "transformation_arrow", "cause_effect", "problem_solution"].includes(template)) {
      const labels = {
        before_after: ["Before", "After"],
        comparison_split: ["A", "B"],
        cause_effect: ["Cause", "Effect"],
        problem_solution: ["Problem", "Response"],
      }[template] || ["From", "To"];
      const leftLabel = P.left_label || labels[0];
      const rightLabel = P.right_label || labels[1];
      // The panels already state the pair; a headline that says it again is cut.
      const headline = headlineUnlessEcho(P.headline || scene.text, [
        `${P.left} → ${P.right}`, `${P.left} ${P.right}`, P.left, P.right,
      ]);
      const head = buildHead(scene, p, P.label || "", headline, { max: 7.6, min: 4.2, maxLines: 2 });
      const bridge = revealAmount(p, scene, 520, 700);

      return structuredFrame(head, band => {
        const pad = 3 * U;
        const bridgeH = 5.4 * U;
        const panelH = Math.min((band.height - bridgeH) / 2, band.hasHead ? 24 * U : 32 * U);
        const fit = fitTogether([String(P.left || ""), String(P.right || "")], band.width - pad * 2, panelH - pad * 2 - 4 * U, {
          max: 6.2, min: 3, weight: 600, tracking: -0.03, leading: 1.16, maxLines: 3,
        });
        // Cards hug their type. A card taller than its content is a hollow box,
        // and the system has no hollow boxes in it.
        const panel = (index, panelLabel, delayMs, hot) => {
          const value = index === 0 ? P.left : P.right;
          const struck = carriesNegation(scene, value, index === 0 ? "left" : "right");
          return `<div style="${frameHolds(scene) ? heldStyle(p, scene) : revealStyle(p, scene, delayMs)}position:relative;display:flex;flex-direction:column;justify-content:center;gap:${px(1.6 * U)};padding:${px(pad)};border-radius:${px(1.6 * U)};background:${hot ? colors.raised : colors.surface};${certaintyBorder(scene, hot ? colors.accent : colors.hairSoft)}">
            <div style="font:600 ${px(MICRO_SIZE)}/1 ${font};letter-spacing:.12em;text-transform:uppercase;color:${hot ? colors.accent : colors.muted};">${esc(String(panelLabel).toUpperCase())}</div>
            <div style="position:relative;font:600 ${px(fit.size)}/${fit.leading} ${font};letter-spacing:-.03em;color:${colors.text};">${esc(fit.wrapped[index].join(" "))}${struck ? strikeThrough(scene, p, value) : ""}</div>
          </div>`;
        };
        const arrow = `<div style="height:${px(bridgeH)};display:flex;align-items:center;gap:${px(1.6 * U)};">
          <div style="height:${px(.34 * U)};width:${px(band.width * 0.24 * bridge)};background:${colors.accent};"></div>
          <div style="opacity:${bridge.toFixed(4)};font:600 ${px(3.8 * U)}/1 ${font};color:${colors.accent};">&#8594;</div></div>`;
        const seat = band.hasHead ? "bottom:0;" : "top:0;bottom:0;justify-content:center;";
        return `<div style="position:absolute;left:0;right:0;${seat}display:flex;flex-direction:column;">
          ${panel(0, leftLabel, 260, false)}${arrow}${panel(1, rightLabel, 640, true)}</div>`;
      });
    }

    // ---- figure family ------------------------------------------------------
    if (["network", "cycle", "hierarchy_tree"].includes(template)) {
      const nodes = items
        .map(node => (typeof node === "object" ? (node.event || node.label || "") : String(node)))
        .filter(Boolean).slice(0, 6);
      const centre = String(P.center || P.parent || "");
      if (centre) {
        for (let index = nodes.length - 1; index >= 0; index--) {
          if (echoes(nodes[index], centre)) nodes.splice(index, 1);
        }
      }
      const headline = headlineUnlessEcho(P.headline || scene.text, nodes.concat([centre]));
      const head = buildHead(scene, p, P.label || (template === "cycle" ? "Feedback loop" : "System"), headline, { max: 7.6, min: 4.2, maxLines: 2 });
      const hub = revealAmount(p, scene, 120, 600);
      const spokes = revealAmount(p, scene, 320, 900);

      return structuredFrame(head, band => {
        // In 9:16 a ring is the wrong figure: four long labels on a circle
        // inscribed in the width leave the bottom of the band empty and collide
        // with the headline. Portrait gets a hub and a rail — the same claim
        // ("these all hang off that") in a shape the frame can actually hold.
        if (!landscape) {
          const railX = 3.2 * U;
          const hubW = band.width;
          const hubFit = fitText(centre, hubW - 6 * U, 11 * U, { max: 4.2, min: BODY_FLOOR, weight: 600, tracking: -0.03, leading: 1.14, maxLines: 3 });
          const hubH = hubFit.height + 6 * U;
          const hubPlate = centre
            ? `<div style="position:absolute;left:0;top:0;width:${px(hubW)};padding:${px(3 * U)};border-radius:${px(1.6 * U)};background:${colors.raised};${certaintyBorder(scene, colors.accent)}opacity:${hub.toFixed(4)};transform:translateY(${px((1 - hub) * 2.4 * U)});font:600 ${px(hubFit.size)}/1.14 ${font};letter-spacing:-.03em;color:${colors.text};">${esc(hubFit.lines.join(" "))}</div>`
            : "";
          const listTop = centre ? hubH + 4 * U : 0;
          const listH = Math.max(8 * U, band.height - listTop);
          const textLeft = railX + 5 * U;
          const fit = fitTogether(nodes, band.width - textLeft, listH / Math.max(1, nodes.length) - 2.4 * U, {
            max: 4, min: BODY_FLOOR, weight: 600, tracking: -0.03, leading: 1.18, maxLines: 2,
          });
          const step = listH / Math.max(1, nodes.length);
          // The rail is drawn to the last node it actually carries, not to an
          // arbitrary fraction of the band.
          const railSpan = step * Math.max(0.5, nodes.length - 0.5);
          const rail = `<div style="position:absolute;left:${px(railX)};top:${px(listTop)};width:${px(.3 * U)};height:${px(railSpan * spokes)};background:${colors.hair};"></div>`;
          const rows = nodes.map((node, index) => {
            const q = revealAmount(p, scene, 480 + index * staggerFor(nodes.length), 600);
            const y = listTop + step * (index + 0.5);
            return `<div style="position:absolute;left:${px(railX)};top:${px(y)};width:${px(3.6 * U)};height:${px(.3 * U)};background:${colors.accent};opacity:${q.toFixed(3)};"></div>
              <div style="position:absolute;left:${px(railX - .9 * U)};top:${px(y - .9 * U)};width:${px(1.8 * U)};height:${px(1.8 * U)};border-radius:50%;background:${colors.accent};opacity:${q.toFixed(3)};"></div>
              <div style="position:absolute;left:${px(textLeft)};width:${px(band.width - textLeft)};top:${px(y)};transform:translateY(-50%);opacity:${q.toFixed(4)};font:600 ${px(fit.size)}/${fit.leading} ${font};letter-spacing:-.03em;color:${colors.text};">${esc(fit.wrapped[index].join(" "))}</div>`;
          }).join("");
          const loop = template === "cycle"
            ? `<div style="position:absolute;left:${px(railX)};top:${px(listTop)};opacity:${spokes.toFixed(3)};transform:translate(-50%,-120%);font:600 ${px(3.2 * U)}/1 ${font};color:${colors.accent};">&#8593;</div>`
            : "";
          return `${hubPlate}${rail}${rows}${loop}`;
        }

        const cx = band.width * 0.5;
        const cy = band.height * 0.5;
        const plateW = Math.min(band.width * 0.42, 26 * U);
        const rx = Math.max(0, band.width * 0.5 - plateW * 0.5);
        const ry = Math.max(0, band.height * 0.5 - 9 * U);
        // One shared size across every node, so the ring reads as one figure.
        const fit = fitTogether(nodes, plateW - 2 * U, 9 * U, { max: 3.6, min: BODY_FLOOR, weight: 600, tracking: -0.02, leading: 1.18, maxLines: 3 });
        let lines = "";
        let plates = "";
        nodes.forEach((node, index) => {
          const angle = -Math.PI / 2 + Math.PI * 2 * index / Math.max(1, nodes.length);
          const x = cx + Math.cos(angle) * rx;
          const y = cy + Math.sin(angle) * ry;
          const q = revealAmount(p, scene, 480 + index * staggerFor(nodes.length), 600);
          if (template === "cycle" && nodes.length > 1) {
            const next = -Math.PI / 2 + Math.PI * 2 * ((index + 1) % nodes.length) / nodes.length;
            lines += `<line x1="${x}" y1="${y}" x2="${cx + Math.cos(next) * rx}" y2="${cy + Math.sin(next) * ry}" stroke="${colors.accent}" stroke-width="${.24 * U}" opacity="${(spokes * .8).toFixed(3)}"/>`;
          } else {
            lines += `<line x1="${cx}" y1="${cy}" x2="${cx + (x - cx) * spokes}" y2="${cy + (y - cy) * spokes}" stroke="${colors.hair}" stroke-width="${.24 * U}"/>`;
          }
          const above = Math.sin(angle) < -0.2;
          plates += `<div style="position:absolute;left:${px(x)};top:${px(y)};transform:translate(-50%,${above ? "-100%" : "0"});opacity:${q.toFixed(4)};display:flex;flex-direction:column;align-items:center;">
              ${above ? "" : `<div style="width:${px(1.8 * U)};height:${px(1.8 * U)};border-radius:50%;background:${colors.accent};margin-bottom:${px(1.2 * U)};"></div>`}
              <div style="width:${px(plateW)};text-align:center;font:600 ${px(fit.size)}/${fit.leading} ${font};letter-spacing:-.02em;color:${colors.body};">${esc(fit.wrapped[index].join(" "))}</div>
              ${above ? `<div style="width:${px(1.8 * U)};height:${px(1.8 * U)};border-radius:50%;background:${colors.accent};margin-top:${px(1.2 * U)};"></div>` : ""}
            </div>`;
        });
        const hubW = Math.min(band.width * 0.44, 28 * U);
        const hubFit = fitText(centre, hubW - 3 * U, 10 * U, { max: 3.8, min: BODY_FLOOR, weight: 600, tracking: -0.02, leading: 1.14, maxLines: 3 });
        const hubPlate = centre
          ? `<div style="position:absolute;left:${px(cx)};top:${px(cy)};transform:translate(-50%,-50%);opacity:${hub.toFixed(4)};width:${px(hubW)};padding:${px(2.2 * U)};border-radius:${px(2.4 * U)};background:${colors.raised};border:1px solid ${colors.accent};text-align:center;font:600 ${px(hubFit.size)}/1.14 ${font};letter-spacing:-.02em;color:${colors.text};">${esc(hubFit.lines.join(" "))}</div>`
          : "";
        return `<svg style="position:absolute;inset:0;" width="${band.width}" height="${band.height}">${lines}</svg>${hubPlate}${plates}`;
      });
    }

    if (template === "bar_chart") {
      const series = arr(P.series).slice(0, 8);
      const max = Math.max(1, ...series.map(item => Number(item.value) || 0));
      const head = buildHead(scene, p, P.unit || "Data", P.headline || scene.text, { max: 7.6, min: 4.2, maxLines: 2 });
      return structuredFrame(head, band => {
        const labelW = band.width * 0.3;
        const rows = series.map((item, index) => {
          const q = revealAmount(p, scene, 260 + index * staggerFor(series.length), 700);
          const share = (Number(item.value) || 0) / max;
          return `<div style="flex:1 1 0;min-height:0;display:flex;align-items:center;gap:${px(2 * U)};border-top:1px solid ${index === 0 ? "transparent" : colors.hairSoft};">
            <div style="flex:0 0 ${px(labelW)};font:600 ${px(2.6 * U)}/1.2 ${font};letter-spacing:.06em;text-transform:uppercase;color:${colors.muted};opacity:${q.toFixed(3)};">${esc(String(item.label || "").toUpperCase())}</div>
            <div style="flex:1 1 auto;display:flex;align-items:center;gap:${px(1.6 * U)};">
              <div style="height:${px(2.6 * U)};width:${pct(share * q * 0.82)};border-radius:${px(.4 * U)};background:${index === 0 ? colors.accent : colors.surface2};border:1px solid ${index === 0 ? colors.accent : colors.hair};"></div>
              <div style="font:600 ${px(3.2 * U)}/1 ${font};letter-spacing:-.02em;color:${colors.text};opacity:${q.toFixed(3)};font-variant-numeric:tabular-nums;">${esc(item.value)}${esc(item.unit || "")}</div>
            </div></div>`;
        }).join("");
        return `<div style="position:absolute;inset:0;display:flex;flex-direction:column;">${rows}</div>`;
      });
    }

    if (template === "audio_wave") {
      const bars = arr(P.energy_bars).slice(0, 64);
      const count = Math.max(1, bars.length);
      const head = buildHead(scene, p, P.label || "Audio structure", P.headline || scene.text, { max: 7.6, min: 4.2, maxLines: 2 });
      return structuredFrame(head, band => {
        const gap = band.width / count * 0.3;
        const barW = (band.width - gap * (count - 1)) / count;
        const html = bars.map((value, index) => {
          const q = revealAmount(p, scene, 200 + index * Math.min(12, staggerFor(bars.length) / 6), 600);
          const height = clamp(Number(value)) * q;
          return `<div style="flex:0 0 ${px(barW)};height:${pct(Math.max(0.02, height))};align-self:center;border-radius:999px;background:${colors.accent};opacity:${(0.4 + 0.6 * q).toFixed(3)};"></div>`;
        }).join("");
        return `<div style="position:absolute;inset:0;display:flex;align-items:center;gap:${px(gap)};">${html}</div>`;
      });
    }

    // ---- fallback: treat anything unmapped as a statement --------------------
    return statementFrame(microLabel(P.label || "", p, scene, 0, undefined, P.headline),
      headlineBlock(P.headline || scene.text, p, scene, { width: box.rail, height: box.height * 0.66 }, { max: 12.4, min: 5.2, maxLines: 5 }),
      scene, p
    );
  }
