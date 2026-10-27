const assert = require('assert');
const {pressOrStop, followStep, runPlan} = require('./glance.cjs');

const page = [{id: '#insurance', text: 'Trip insurance'}, {id: '#reserve', text: 'Reserve'}];
const kept = pressOrStop('Reserve', page);
assert.equal(kept.action, 'press');
assert.equal(kept.control.id, '#reserve');
assert.equal(kept.extra, 1);

const gone = pressOrStop('Reserve', [{id: '#insurance', text: 'Trip insurance'}]);
assert.equal(gone.action, 'stop');
assert.equal(gone.reason, 'the old button is gone');

const doubled = pressOrStop('Reserve', [{id: '#a', text: 'Reserve'}, {id: '#b', text: 'Reserve'}]);
assert.equal(doubled.reason, 'the old button appears more than once');

const backup = pressOrStop('Reserve', [{id: '#go', text: 'Continue'}], ['Continue']);
assert.equal(backup.control.id, '#go');
assert.equal(backup.matched, 'Continue');

let calls = 0;
const saved = followStep('book a table', {text: 'Reserve'}, page, [], () => { calls += 1; return 'Trip insurance'; });
assert.equal(saved.control.id, '#reserve');
assert.equal(calls, 0);

const seen = [];
const repaired = followStep('book a table', {text: 'Confirm'}, [{id: '#go', text: 'Continue'}], [], (packet) => { seen.push(packet); return 'Continue'; }, [], null, 1);
assert.equal(repaired.control.id, '#go');
assert.equal(seen[0].instruction, 'book a table');
assert.equal(JSON.stringify(seen[0]).includes('Confirm'), false);

const steps = [{text: 'Date', check: 'Date set'}, {text: 'Confirm', check: 'Held'}];
const first = runPlan({
  goal: 'book a table',
  steps,
  pages: [
    {controls: [{id: 'date', text: 'Date'}], after: 'Date set'},
    {controls: [{id: 'go', text: 'Continue'}, {id: 'a', text: 'Seating'}], after: 'Held for 7'},
  ],
  model: () => 'Continue',
});
assert.equal(first.presses.join(','), 'date,go');
assert.equal(first.asked, 1);
assert.equal(first.steps[1].text, 'Confirm');
const second = runPlan({
  goal: 'book a table',
  steps,
  pages: [
    {controls: [{id: 'date', text: 'Date'}], after: 'Date set'},
    {controls: [{id: 'go', text: 'Continue'}, {id: 'b', text: 'Insurance'}], after: 'Held for 8'},
  ],
  model: () => 'Continue',
  book: first.book,
});
assert.equal(second.steps[0].text, 'Date');
assert.equal(second.steps[1].text, 'Continue');

const wrongRoom = runPlan({
  goal: 'book a table',
  steps: [{text: 'Next', check: 'Tuesday'}, {text: 'Pay'}],
  pages: [{controls: [{id: 'n', text: 'Next'}], after: 'Wednesday'}],
});
assert.equal(wrongRoom.reason, 'the job did not happen');
assert.equal(wrongRoom.presses.join(','), 'n');
assert.equal(wrongRoom.actions.length, 1);

console.log('web glance ok');
