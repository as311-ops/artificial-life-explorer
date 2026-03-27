// Opcode color LUT matching main.py:151-171
// Maps normalized byte values to RGB colors

export const OPCODE_CHARS = '<>{}-+.,[]' as const;
export const OPCODE_BYTES = Array.from(OPCODE_CHARS).map(c => c.charCodeAt(0));

// RGB palette indexed by opcode character order
export const PALETTE: [number, number, number][] = [
  [239, 71, 111],   // < (LT)
  [255, 209, 102],  // > (GT)
  [6, 214, 160],    // { (LB)
  [17, 138, 178],   // } (RB)
  [255, 127, 80],   // - (MINUS)
  [131, 56, 236],   // + (PLUS)
  [58, 134, 255],   // . (DOT)
  [255, 190, 11],   // , (COMMA)
  [139, 201, 38],   // [ (LBRACK)
  [255, 89, 94],    // ] (RBRACK)
];

export const NON_OPCODE_COLOR: [number, number, number] = [20, 20, 20];

// Build a 256-entry color lookup table (each entry = [R, G, B])
export function buildColorLUT(): Uint8Array {
  // 256 entries x 3 channels = 768 bytes
  const lut = new Uint8Array(256 * 3);
  // Fill with non-opcode color
  for (let i = 0; i < 256; i++) {
    lut[i * 3] = NON_OPCODE_COLOR[0];
    lut[i * 3 + 1] = NON_OPCODE_COLOR[1];
    lut[i * 3 + 2] = NON_OPCODE_COLOR[2];
  }
  // Set opcode colors
  OPCODE_BYTES.forEach((byte, idx) => {
    lut[byte * 3] = PALETTE[idx][0];
    lut[byte * 3 + 1] = PALETTE[idx][1];
    lut[byte * 3 + 2] = PALETTE[idx][2];
  });
  return lut;
}
