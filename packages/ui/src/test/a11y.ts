import axe from 'axe-core';
import { expect } from 'vitest';

/** Run axe on a rendered container; fail on serious/critical violations (TS-A11Y-01). */
export async function expectNoA11yViolations(container: Element) {
  const result = await axe.run(container, {
    rules: { 'color-contrast': { enabled: false } }, // jsdom has no layout; contrast is covered by token tests
  });
  const bad = result.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical');
  expect(bad.map((v) => `${v.id}: ${v.help} (${v.nodes.map((n) => n.target.join(' ')).join(', ')})`)).toEqual([]);
}
