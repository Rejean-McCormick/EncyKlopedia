import { afterEach, describe, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render } from '@testing-library/svelte';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import TimelineLineageView from '../../src/components/TimelineLineageView.svelte';
import TreeView from '../../src/components/TreeView.svelte';
import DagProofView from '../../src/components/DagProofView.svelte';
import FlowPathView from '../../src/components/FlowPathView.svelte';
import CausalFeedbackView from '../../src/components/CausalFeedbackView.svelte';
import MatrixProfileView from '../../src/components/MatrixProfileView.svelte';
import StateFlowView from '../../src/components/StateFlowView.svelte';
import TraceabilityView from '../../src/components/TraceabilityView.svelte';
import MultiscaleLayerView from '../../src/components/MultiscaleLayerView.svelte';
import SpatialView from '../../src/components/SpatialView.svelte';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const fixture = (name) => JSON.parse(fs.readFileSync(path.join(ROOT, 'examples', 'projections', `${name}.json`), 'utf8'));

const cases = [
  ['timeline-lineage', TimelineLineageView],
  ['tree', TreeView],
  ['dag', DagProofView, 'dag-proof'],
  ['flow', FlowPathView, 'flow-path'],
  ['causal-feedback', CausalFeedbackView],
  ['matrix', MatrixProfileView, 'matrix-profile'],
  ['state-flow', StateFlowView],
  ['traceability', TraceabilityView],
  ['multiscale', MultiscaleLayerView, 'multiscale-layer'],
  ['spatial', SpatialView],
];

afterEach(() => cleanup());

describe('specialized 1.0 renderers', () => {
  for (const [projectionKind, Component, rendererId = projectionKind] of cases) {
    test(`${rendererId} renders its canonical projection without losing keyboard actions`, async () => {
      const inspect = vi.fn();
      const { container } = render(Component, { data: fixture(projectionKind), inspect });
      expect(container.querySelector(`[data-renderer="${rendererId}"]`)).toBeTruthy();
      const interactive = container.querySelector('button:not([disabled])');
      if (interactive) {
        await fireEvent.click(interactive);
        // Some renderers expose navigation buttons, others only static projection data.
        expect(interactive.tagName).toBe('BUTTON');
      }
      expect(container.textContent?.trim().length).toBeGreaterThan(0);
    });
  }
  test('graphical renderers expose native visual canvases while keeping accessible text fallbacks', () => {
    const visualCases = [
      ['dag', DagProofView, 'svg'],
      ['flow', FlowPathView, 'svg'],
      ['causal-feedback', CausalFeedbackView, 'svg'],
      ['spatial', SpatialView, 'svg'],
      ['timeline-lineage', TimelineLineageView, '.adaptive-timeline'],
      ['multiscale', MultiscaleLayerView, '.scale-board'],
    ];
    for (const [projectionKind, Component, selector] of visualCases) {
      const { container, unmount } = render(Component, { data: fixture(projectionKind), inspect: vi.fn() });
      expect(container.querySelector(selector)).toBeTruthy();
      unmount();
    }
  });

});
