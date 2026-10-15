// one_pass_form.js — fill a whole multi-page form from an answer sheet in ONE pass.
// From the 2026-10-14 deep-research report (sections B and "Concrete commands"), re-typed clean.
// Inject into a tab via CDP Runtime.evaluate with awaitPromise:true, returnByValue:true, userGesture:true:
//   `(${runOnePassForm.toString()})(${JSON.stringify(answerSheet)})`
// Returns one of: SUBMITTED | STOPPED_UNANSWERED_REQUIRED (with the list) | HALTED_NO_NEXT_BUTTON | MAX_STEPS_EXCEEDED
// It never comes back to the model between steps. It only stops on a question the sheet cannot answer.

async function runOnePassForm(answerSheet, maxSteps = 12) {
  const sleep = (ms) => new Promise(r => setTimeout(r, ms + Math.floor(Math.random() * 60)));
  const PLACEHOLDER_RE = /^(select|choose|please select|--|none|select an option)/i;

  function setNativeValue(el, val) {
    const proto = el instanceof HTMLSelectElement ? HTMLSelectElement.prototype
                : el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype
                : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    el.focus();
    if (setter) setter.call(el, val); else el.value = val;
    el.dispatchEvent(new InputEvent('input', { bubbles: true, data: String(val) }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    el.blur();
  }

  function matchAnswer(label, type) {
    const norm = label.toLowerCase().trim();
    for (const [pattern, val] of Object.entries(answerSheet.exact || {})) {
      if (val !== '' && norm.includes(pattern.toLowerCase())) return val;
    }
    if (type === 'number' || /\b(years|experience|how many|salary|compensation)\b/i.test(norm)) {
      return answerSheet.defaults?.number ?? '5';
    }
    if (type === 'yesno' || /\b(authorized|sponsorship|legally|relocate|comfortable|agree)\b/i.test(norm)) {
      return answerSheet.defaults?.yesNo ?? 'Yes';
    }
    return answerSheet.defaults?.text ?? null;
  }

  for (let step = 1; step <= maxSteps; step++) {
    await sleep(350);
    const missingRequired = [];

    // 1. native <select> (the "Select an option" trap)
    for (const sel of document.querySelectorAll('select')) {
      if (sel.offsetParent === null) continue;
      const label = (sel.labels?.[0]?.innerText || sel.getAttribute('aria-label') || sel.name || '').trim();
      const currentText = sel.options[sel.selectedIndex]?.text?.trim() || '';
      const isUnanswered = !sel.value || PLACEHOLDER_RE.test(currentText);
      if (isUnanswered) {
        const target = matchAnswer(label, 'select');
        if (target !== null) {
          const t = String(target).toLowerCase();
          const opt = Array.from(sel.options).find(o =>
            !PLACEHOLDER_RE.test(o.text.trim()) &&
            (o.text.toLowerCase().includes(t) || o.value.toLowerCase() === t));
          if (opt) setNativeValue(sel, opt.value);
        }
      }
      const afterText = sel.options[sel.selectedIndex]?.text?.trim() || '';
      if ((sel.required || sel.getAttribute('aria-required') === 'true') && (!sel.value || PLACEHOLDER_RE.test(afterText))) {
        missingRequired.push({ kind: 'select', label, options: Array.from(sel.options).map(o => o.text.trim()) });
      }
    }

    // 2. radio groups
    const radioNames = new Set(Array.from(document.querySelectorAll('input[type="radio"]')).map(r => r.name).filter(Boolean));
    for (const name of radioNames) {
      const radios = Array.from(document.querySelectorAll(`input[type="radio"][name="${CSS.escape(name)}"]`));
      if (radios.some(r => r.checked)) continue;
      const groupLabel = (radios[0].closest('fieldset')?.querySelector('legend')?.innerText || name).trim();
      const target = matchAnswer(groupLabel, 'yesno');
      const match = radios.find(r => (r.labels?.[0]?.innerText || r.value || '').toLowerCase().includes(String(target).toLowerCase()));
      if (match) { match.focus(); match.click(); match.dispatchEvent(new Event('change', { bubbles: true })); }
      else if (radios.some(r => r.required)) missingRequired.push({ kind: 'radio', label: groupLabel });
    }

    // 3. text / number inputs and textareas
    for (const inp of document.querySelectorAll('input:not([type="hidden"]):not([type="radio"]):not([type="checkbox"]):not([type="file"]), textarea')) {
      if (inp.offsetParent === null || inp.disabled || inp.readOnly || inp.value.trim() !== '') continue;
      const label = (inp.labels?.[0]?.innerText || inp.getAttribute('aria-label') || inp.placeholder || inp.name || '').trim();
      const target = matchAnswer(label, inp.type === 'number' ? 'number' : 'text');
      if (target !== null) { setNativeValue(inp, String(target)); await sleep(40); }
      if ((inp.required || inp.getAttribute('aria-required') === 'true') && inp.value.trim() === '') {
        missingRequired.push({ kind: inp.type || 'text', label });
      }
    }

    if (missingRequired.length > 0) {
      return { status: 'STOPPED_UNANSWERED_REQUIRED', step, missingRequired, url: location.href };
    }

    // 4. advance or submit
    const buttons = Array.from(document.querySelectorAll('button, input[type="submit"], [role="button"]'))
      .filter(b => b.offsetParent !== null && !b.disabled);
    const submitBtn = buttons.find(b => /\b(submit application|submit|send application|finish)\b/i.test(b.innerText || b.value || ''));
    if (submitBtn) {
      submitBtn.click();
      await sleep(1200);
      return { status: 'SUBMITTED', stepsTaken: step, url: location.href };
    }
    const nextBtn = buttons.find(b => /\b(next|continue|review|save and continue)\b/i.test(b.innerText || b.value || ''));
    if (!nextBtn) return { status: 'HALTED_NO_NEXT_BUTTON', step, url: location.href };
    nextBtn.click();
  }
  return { status: 'MAX_STEPS_EXCEEDED', url: location.href };
}

if (typeof module !== 'undefined') module.exports = { runOnePassForm };
