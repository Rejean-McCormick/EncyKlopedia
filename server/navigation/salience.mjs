import { compare } from '../pack.mjs';

const log = (n) => Math.log1p(Math.max(0, n || 0));
const round = (n) => Math.round(n * 1000) / 1000;

function jaccard(a = [], b = []) {
  const aa = new Set(a), bb = new Set(b);
  if (!aa.size && !bb.size) return 0;
  let intersection = 0;
  for (const x of aa) if (bb.has(x)) intersection++;
  return intersection / (aa.size + bb.size - intersection);
}

function similarity(a, b) {
  return Math.max(
    jaccard(a.evidence?.assertionRefs, b.evidence?.assertionRefs),
    jaccard(a.evidence?.entityRefs, b.evidence?.entityRefs),
    jaccard(a.evidence?.sourceRefs, b.evidence?.sourceRefs),
  );
}

export function baseSalience(candidate) {
  const e = candidate.evidence || {};
  return (
    (candidate.priority ?? 0.5) * 10 +
    log(e.assertionRefs?.length) * 3 +
    log(e.entityRefs?.length) * 2 +
    log(e.sourceRefs?.length) * 1.5 +
    (candidate.directness ?? 0.5)
  );
}

export function rankCandidates(candidates, limit) {
  const unique = [...new Map(candidates.map((c) => [c.id, c])).values()].map((c) => ({
    ...c,
    _base: baseSalience(c),
  }));
  const selected = [];
  const remaining = [...unique];
  while (selected.length < limit && remaining.length) {
    let best = null;
    let bestIndex = -1;
    for (let i = 0; i < remaining.length; i++) {
      const c = remaining[i];
      const redundancy = selected.length ? Math.max(...selected.map((x) => similarity(c, x))) : 0;
      const adjusted = c._base - redundancy * 3.5;
      if (
        !best ||
        adjusted > best.adjusted ||
        (adjusted === best.adjusted && compare(c.label, best.candidate.label) < 0) ||
        (adjusted === best.adjusted && c.label === best.candidate.label && compare(c.id, best.candidate.id) < 0)
      ) {
        best = { candidate: c, adjusted, redundancy };
        bestIndex = i;
      }
    }
    const [picked] = remaining.splice(bestIndex, 1);
    selected.push({
      ...picked,
      salience: {
        score: round(best.adjusted),
        base: round(picked._base),
        redundancy: round(best.redundancy),
        signals: {
          assertions: picked.evidence?.assertionRefs?.length || 0,
          entities: picked.evidence?.entityRefs?.length || 0,
          sources: picked.evidence?.sourceRefs?.length || 0,
          priority: picked.priority ?? 0.5,
        },
      },
    });
  }
  return selected.map(({ _base, ...c }) => c);
}
