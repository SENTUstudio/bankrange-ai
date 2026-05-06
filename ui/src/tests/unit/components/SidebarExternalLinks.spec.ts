import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mount } from 'svelte';
import SidebarExternalLinks from '$lib/components/sidebar/SidebarExternalLinks.svelte';

describe('SidebarExternalLinks', () => {
  let container: HTMLDivElement;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
  });

  afterEach(() => {
    document.body.removeChild(container);
  });

  it('renders 3 external links', () => {
    mount(SidebarExternalLinks, { target: container });
    const links = container.querySelectorAll('a');
    expect(links).toHaveLength(3);
  });

  it('Grafana link has correct href', () => {
    mount(SidebarExternalLinks, { target: container });
    const links = container.querySelectorAll('a');
    expect(links[0].getAttribute('href')).toBe('http://localhost:3000');
  });

  it('Kafka UI link has correct href', () => {
    mount(SidebarExternalLinks, { target: container });
    const links = container.querySelectorAll('a');
    expect(links[1].getAttribute('href')).toBe('http://localhost:8081');
  });

  it('API Docs link has correct href', () => {
    mount(SidebarExternalLinks, { target: container });
    const links = container.querySelectorAll('a');
    expect(links[2].getAttribute('href')).toBe('http://localhost:8000/docs');
  });

  it('all links use target="_blank"', () => {
    mount(SidebarExternalLinks, { target: container });
    const links = container.querySelectorAll('a');
    links.forEach((link) => {
      expect(link.getAttribute('target')).toBe('_blank');
    });
  });

  it('all links use rel="noopener noreferrer"', () => {
    mount(SidebarExternalLinks, { target: container });
    const links = container.querySelectorAll('a');
    links.forEach((link) => {
      expect(link.getAttribute('rel')).toBe('noopener noreferrer');
    });
  });

  it('section heading "External" is rendered', () => {
    mount(SidebarExternalLinks, { target: container });
    expect(container.textContent).toContain('External');
  });
});
