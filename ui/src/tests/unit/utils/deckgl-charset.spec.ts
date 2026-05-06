import { describe, it, expect } from 'vitest';
import { SPANISH_CHARS, ASCII_PRINTABLE, getTextLayerCharacterSet } from '$lib/utils/deckgl-charset';

describe('deckgl-charset', () => {
  it('should include ASCII printable characters (32-126)', () => {
    expect(ASCII_PRINTABLE).toContain('A');
    expect(ASCII_PRINTABLE).toContain('z');
    expect(ASCII_PRINTABLE).toContain(' ');
    expect(ASCII_PRINTABLE).toContain('~');
    expect(ASCII_PRINTABLE).toHaveLength(95);
  });

  it('should include Spanish accented characters', () => {
    expect(SPANISH_CHARS).toContain('ó');
    expect(SPANISH_CHARS).toContain('á');
    expect(SPANISH_CHARS).toContain('ú');
    expect(SPANISH_CHARS).toContain('é');
    expect(SPANISH_CHARS).toContain('í');
    expect(SPANISH_CHARS).toContain('ñ');
    expect(SPANISH_CHARS).toContain('ü');
    expect(SPANISH_CHARS).toContain('Á');
    expect(SPANISH_CHARS).toContain('É');
    expect(SPANISH_CHARS).toContain('Í');
    expect(SPANISH_CHARS).toContain('Ó');
    expect(SPANISH_CHARS).toContain('Ú');
    expect(SPANISH_CHARS).toContain('Ñ');
    expect(SPANISH_CHARS).toContain('Ü');
  });

  it('should combine ASCII and Spanish chars in characterSet', () => {
    const set = getTextLayerCharacterSet();
    expect(set).toContain('ó');
    expect(set).toContain('á');
    expect(set).toContain('ú');
    expect(set).toContain('M'); // ASCII check
    expect(set).toContain(' ');  // space
    expect(set).toHaveLength(95 + 14);
  });
});
