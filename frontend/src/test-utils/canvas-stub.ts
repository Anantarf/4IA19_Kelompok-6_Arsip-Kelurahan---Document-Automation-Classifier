// Minimal stub for node `canvas` native module used by some libraries in test env
export class Canvas {
  constructor() {}
}
export function createCanvas(width: number, height: number) {
  return new Canvas();
}
export default { Canvas, createCanvas } as any;
