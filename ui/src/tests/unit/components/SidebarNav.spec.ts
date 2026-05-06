import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mount, unmount } from 'svelte';
import SidebarNav from '$lib/components/sidebar/SidebarNav.svelte';

describe('SidebarNav', () => {
  let container: HTMLDivElement;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
  });

  afterEach(() => {
    document.body.removeChild(container);
  });

  it('renders 3 navigation items', () => {
    mount(SidebarNav, { target: container });
    const links = container.querySelectorAll('a');
    expect(links).toHaveLength(3);
  });

  it('first item (Dashboard) has active class', () => {
    mount(SidebarNav, { target: container });
    const links = container.querySelectorAll('a');
    expect(links[0].className).toContain('text-brand-cyan');
    expect(links[0].className).toContain('bg-brand-cyan-10');
  });

  it('each link has correct href', () => {
    mount(SidebarNav, { target: container });
    const links = container.querySelectorAll('a');
    expect(links[0].getAttribute('href')).toBe('/');
    expect(links[1].getAttribute('href')).toBe('/logs');
    expect(links[2].getAttribute('href')).toBe('/settings');
  });

  it('section heading "Navigation" is rendered', () => {
    mount(SidebarNav, { target: container });
    expect(container.textContent).toContain('Navigation');
  });

  it('all links use target="_self"', () => {
    mount(SidebarNav, { target: container });
    const links = container.querySelectorAll('a');
    links.forEach((link) => {
      expect(link.getAttribute('target')).toBe('_self');
    });
  });
});
