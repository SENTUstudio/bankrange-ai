export const ASCII_PRINTABLE = Array.from({ length: 95 }, (_, i) => String.fromCharCode(32 + i));
export const SPANISH_CHARS = Array.from('áéíóúñüÁÉÍÓÚÑÜ');

export function getTextLayerCharacterSet(): string[] {
  return [...ASCII_PRINTABLE, ...SPANISH_CHARS];
}
