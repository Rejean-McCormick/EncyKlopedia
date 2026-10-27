export function layoutConstellation(items, width = 900, height = 560, centerX = width / 2, centerY = height / 2) {
  const cx = centerX;
  const cy = centerY;
  const n = items.length;
  if (!n) return [];
  const place = (slice, rx, ry, offset, ring) =>
    slice.map((item, i) => {
      const angle = offset + (i * Math.PI * 2) / slice.length;
      return {
        ...item,
        x: cx + rx * Math.cos(angle),
        y: cy + ry * Math.sin(angle),
        ring,
      };
    });
  if (n <= 10) return place(items, Math.min(350, width * 0.36), Math.min(215, height * 0.35), -Math.PI / 2, 1);
  const innerCount = Math.min(8, Math.max(6, Math.round(n * 0.34)));
  return [
    ...place(items.slice(0, innerCount), Math.min(245, width * 0.25), Math.min(160, height * 0.27), -Math.PI / 2, 1),
    ...place(items.slice(innerCount), Math.min(405, width * 0.43), Math.min(255, height * 0.42), -Math.PI / 2 + 0.13, 2),
  ];
}

export function splitLabel(label, max = 19) {
  const text = String(label || '');
  if (text.length <= max) return [text];
  const words = text.split(/\s+/);
  const lines = [''];
  for (const word of words) {
    const i = lines.length - 1;
    const next = (lines[i] + ' ' + word).trim();
    if (next.length <= max || !lines[i]) lines[i] = next;
    else if (lines.length < 2) lines.push(word);
    else {
      lines[i] = (lines[i] + ' ' + word).trim();
      break;
    }
  }
  return lines.map((line) => (line.length > max + 5 ? line.slice(0, max + 4) + '…' : line));
}
