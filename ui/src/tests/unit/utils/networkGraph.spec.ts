import { describe, it, expect } from 'vitest';
import { getNodeShape, getNodeColor, hexagonPoints, diamondPoints } from '$lib/utils/networkGraph';

describe('networkGraph utils', () => {
  describe('getNodeShape', () => {
    it('returns rect for router', () => {
      expect(getNodeShape('router')).toBe('rect');
    });
    it('returns polygon for switch', () => {
      expect(getNodeShape('switch')).toBe('polygon');
    });
    it('returns polygon for segment', () => {
      expect(getNodeShape('segment')).toBe('polygon');
    });
    it('returns circle for workstation', () => {
      expect(getNodeShape('workstation')).toBe('circle');
    });
  });

  describe('getNodeColor', () => {
    it('returns orange for router', () => {
      expect(getNodeColor('router')).toBe('#ffaa00');
    });
    it('returns blue for switch', () => {
      expect(getNodeColor('switch')).toBe('#00aaff');
    });
    it('returns green for workstation', () => {
      expect(getNodeColor('workstation')).toBe('#33ff33');
    });
    it('returns pink for segment', () => {
      expect(getNodeColor('segment')).toBe('#ff66cc');
    });
  });

  describe('hexagonPoints', () => {
    it('produces 6 comma-separated coordinates', () => {
      const pts = hexagonPoints(0, 0, 10);
      const pairs = pts.split(' ');
      expect(pairs.length).toBe(6);
      for (const p of pairs) {
        expect(p).toMatch(/^-?\d+(\.\d+)?(e-?\d+)?,-?\d+(\.\d+)?(e-?\d+)?$/);
      }
    });
  });

  describe('diamondPoints', () => {
    it('produces 4 comma-separated coordinates', () => {
      const pts = diamondPoints(0, 0, 10);
      const pairs = pts.split(' ');
      expect(pairs.length).toBe(4);
      for (const p of pairs) {
        expect(p).toMatch(/^-?\d+(\.\d+)?(e-?\d+)?,-?\d+(\.\d+)?(e-?\d+)?$/);
      }
    });
  });
});
