// Fast look for a saved web step. Exact button name. Extra buttons do not count.
function label(control) {
  for (const key of ['text', 'label', 'name', 'description']) {
    const value = control && control[key];
    if (typeof value === 'string' && value.trim()) return value.trim();
  }
  return '';
}

function pressOrStop(wanted, controls, backups = []) {
  if (typeof wanted !== 'string' || !wanted.trim()) throw new Error('need the button the task learned');
  if (!Array.isArray(controls)) throw new Error('need the live page buttons');
  const names = [];
  const seen = new Set();
  for (const name of [wanted, ...backups]) {
    if (typeof name !== 'string' || !name.trim()) continue;
    const key = name.trim().toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    names.push(name.trim());
  }
  for (const name of names) {
    const hits = controls.filter(control => label(control).toLowerCase() === name.toLowerCase());
    if (hits.length > 1) return {action: 'stop', reason: 'the old button appears more than once', page: controls};
    if (hits.length === 1 && typeof hits[0].id === 'string' && hits[0].id) {
      return {action: 'press', control: hits[0], matched: name, extra: controls.length - 1};
    }
  }
  return {action: 'stop', reason: 'the old button is gone', page: controls};
}

function pageKey(controls) {
  return controls.map(label).filter(Boolean).map(name => name.toLowerCase()).sort().join('|');
}

function unlabeled(controls) {
  const rows = controls.filter(control => control && typeof control === 'object');
  return rows.length > 0 && rows.every(control => !label(control));
}

function packetFor(goal, controls, actions, picture) {
  const page = {controls};
  if (picture) page.picture = picture;
  if (unlabeled(controls)) page.needs_picture = true;
  return {instruction: goal, observations: [page], actions};
}

function followStep(goal, step, controls, actions = [], model = null, failures = [], picture = null, stepIndex = 0) {
  const wanted = step.saved || step.text || '';
  const decision = pressOrStop(wanted, controls, step.backups || []);
  if (decision.action === 'press') return {...decision, via: 'saved'};
  const trace = actions.concat([{step: stepIndex, status: 'missed', cause: decision.reason}]);
  if (unlabeled(controls) && !picture) return {action: 'stop', reason: 'need a picture', page: controls, via: 'saved'};
  const packet = packetFor(goal, controls, trace, picture);
  if (!model) return {...decision, via: 'saved', packet};
  const answer = model(packet);
  if (typeof answer !== 'string' || !answer.trim()) {
    return {action: 'stop', reason: 'the model gave no button', page: controls, packet, via: 'model'};
  }
  const name = answer.trim();
  const signature = pageKey(controls);
  if (failures.some(failure => failure.page === signature && String(failure.button || '').toLowerCase() === name.toLowerCase())) {
    return {action: 'stop', reason: 'that button already failed on this page', page: controls, packet, via: 'model'};
  }
  const pressed = pressOrStop(name, controls);
  if (pressed.action !== 'press') {
    return {action: 'stop', reason: 'the new button is not on the page', page: controls, packet, rejected: name, via: 'model'};
  }
  return {...pressed, via: 'model', packet};
}

function noteHit(book, stepIndex, controls, button) {
  const fresh = JSON.parse(JSON.stringify(book && typeof book === 'object' ? book : {}));
  const key = String(stepIndex);
  fresh[key] = fresh[key] && typeof fresh[key] === 'object' ? fresh[key] : {};
  const pages = Array.isArray(fresh[key][button]) ? fresh[key][button] : [];
  const signature = pageKey(controls);
  if (signature && !pages.includes(signature)) pages.push(signature);
  fresh[key][button] = pages;
  return {book: fresh, admitted: pages.length >= 2 ? button : null};
}

function writeButton(step, button) {
  if (Object.prototype.hasOwnProperty.call(step, 'text')) step.text = button;
  else if (Object.prototype.hasOwnProperty.call(step, 'saved')) step.saved = button;
  else step.text = button;
}

function jobText(after) {
  if (after == null) return '';
  if (typeof after === 'string') return after;
  if (Array.isArray(after)) return after.map(label).join(' ');
  if (typeof after === 'object') return jobText(after.text || after.controls);
  return '';
}

function jobHappened(step, after) {
  const check = step && step.check;
  if (typeof check !== 'string' || !check.trim()) return null;
  return jobText(after).toLowerCase().includes(check.trim().toLowerCase());
}

function runPlan({goal, steps, pages, model = null, book = {}, failures = []}) {
  const freshSteps = JSON.parse(JSON.stringify(steps));
  let freshBook = JSON.parse(JSON.stringify(book || {}));
  const seen = failures.slice();
  const presses = [];
  const actions = [];
  let asked = 0;
  const counting = model ? (packet) => { asked += 1; return model(packet); } : null;
  for (let index = 0; index < freshSteps.length; index += 1) {
    if (index >= pages.length) {
      return {status: 'stopped', reason: 'the page ended', presses, actions, steps: freshSteps, book: freshBook, failures: seen, asked};
    }
    const page = pages[index];
    const controls = page.controls || page;
    const picture = page.picture || null;
    const before = JSON.parse(JSON.stringify(freshSteps));
    const decision = followStep(goal, freshSteps[index], controls, actions, counting, seen, picture, index);
    if (decision.action !== 'press') {
      if (decision.rejected) seen.push({page: pageKey(controls), button: decision.rejected, step: index});
      actions.push({step: index, status: 'missed', cause: decision.reason || 'this step missed'});
      return {status: 'stopped', reason: decision.reason, presses, actions, steps: freshSteps, book: freshBook, failures: seen, packet: decision.packet, asked};
    }
    presses.push(decision.control.id);
    actions.push({step: index, status: 'pressed'});
    const happened = jobHappened(freshSteps[index], page.after);
    if (happened === false) {
      actions[actions.length - 1] = {step: index, status: 'missed', cause: 'the job did not happen'};
      return {status: 'stopped', reason: 'the job did not happen', presses, actions, steps: freshSteps, book: freshBook, failures: seen, asked};
    }
    if (decision.via === 'model' && happened === true) {
      const noted = noteHit(freshBook, index, controls, decision.matched);
      freshBook = noted.book;
      if (noted.admitted) {
        writeButton(freshSteps[index], noted.admitted);
        freshSteps.forEach((_, other) => { if (other !== index) freshSteps[other] = before[other]; });
      }
    }
  }
  return {status: 'done', presses, actions, steps: freshSteps, book: freshBook, failures: seen, asked};
}

module.exports = {pressOrStop, followStep, noteHit, runPlan, writeButton, jobHappened};
