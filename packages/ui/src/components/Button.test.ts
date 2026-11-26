import { render, screen } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import Button from './Button.svelte';
import { expectNoA11yViolations } from '../test/a11y';

describe('Button', () => {
  it('renders text and fires click', async () => {
    const onclick = vi.fn();
    render(Button, { text: 'Search', onclick });
    const b = screen.getByRole('button', { name: 'Search' });
    b.click();
    expect(onclick).toHaveBeenCalledOnce();
  });
  it('icon-only uses label as accessible name', async () => {
    const { container } = render(Button, { icon: 'share', label: 'Share' });
    expect(screen.getByRole('button', { name: 'Share' })).toBeInTheDocument();
    await expectNoA11yViolations(container);
  });
  it('loading disables and announces', () => {
    render(Button, { text: 'Ask', loading: true, loadingLabel: 'Loading' });
    const b = screen.getByRole('button');
    expect(b).toBeDisabled();
    expect(b).toHaveAttribute('aria-busy', 'true');
  });
  it('renders a link when href is set', () => {
    render(Button, { href: '/en/p/x', text: 'View passage' });
    expect(screen.getByRole('link', { name: 'View passage' })).toHaveAttribute('href', '/en/p/x');
  });
  it('exposes pressed state for toggles', () => {
    render(Button, { text: 'Then', pressed: true });
    expect(screen.getByRole('button', { name: 'Then' })).toHaveAttribute('aria-pressed', 'true');
  });
});
