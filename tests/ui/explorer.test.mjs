import { beforeEach, afterEach, test, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, cleanup, within } from '@testing-library/svelte';
import Explorer from '../../src/components/Explorer.svelte';
import { Engine } from '../../server/engine.mjs';
import { loadPack } from '../../server/pack.mjs';
import { loadLenses } from '../../server/index.mjs';
import { buildCommunicationRequest } from '../../server/integrations/semantik.mjs';
import { validate } from '../../server/contracts.mjs';
let engine, lenses;
beforeEach(() => {
  localStorage.clear();
  engine = new Engine(loadPack());
  lenses = loadLenses(engine);
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url, options = {}) => {
      const data = options.body ? JSON.parse(options.body) : null;
      let value;
      try {
        switch (url) {
          case '/api/sa/request':
            value = buildCommunicationRequest(engine, data);
            break;
          case '/api/bootstrap':
            value = engine.bootstrap(lenses);
            break;
          case '/api/query':
            value = engine.query(data.query, data.cursor);
            break;
          case '/api/facets':
            value = engine.facets(data.query, data.relations);
            break;
          case '/api/entity':
            value = engine.entity(data.id, data.context);
            break;
          case '/api/constellation':
            value = engine.constellation(data, lenses);
            break;
          case '/api/navigation/plan':
            value = engine.navigationPlan(data, lenses);
            break;
          case '/api/navigation/project':
            value = engine.navigationProjection(data, lenses);
            break;
          case '/api/validate-state':
            validate('exploration-state', data);
            engine.check(data.query);
            value = { valid: true };
            break;
          default:
            throw Error('Unknown endpoint');
        }
        return { ok: true, json: async () => value };
      } catch (e) {
        return { ok: false, json: async () => ({ error: { message: e.message } }) };
      }
    }),
  );
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
async function ready() {
  render(Explorer);
  await waitFor(() => expect(document.querySelector('.result-count')?.textContent).toBe('132'));
  await waitFor(() =>
    expect(document.querySelector('.results-body').getAttribute('aria-busy')).toBe('false'),
  );
}
async function done() {
  await waitFor(() =>
    expect(document.querySelector('.results-body').getAttribute('aria-busy')).toBe('false'),
  );
}
test('renders the explorer and filters without hiding criteria on lens change', async () => {
  await ready();
  expect(screen.getByText('Corpus de démonstration')).toBeTruthy();
  const checkbox = screen.getByRole('checkbox', { name: /Philosophie/ });
  await fireEvent.click(checkbox);
  await done();
  expect(document.querySelector('.active-filters').textContent).toContain('Philosophie');
  await fireEvent.change(screen.getByLabelText('Perspective'), {
    target: { value: 'sociodemography' },
  });
  await done();
  expect(document.querySelector('.hidden-filters-note').textContent).toContain('1 critère');
  expect(document.querySelector('.active-filters').textContent).toContain('Philosophie');
  expect(screen.getAllByRole('checkbox', { name: /Afrique du Nord/ })[0]).toBeTruthy();
});
test('pivots complete selection, records undo and switches views', async () => {
  await ready();
  await fireEvent.change(screen.getByLabelText('Explorer une relation'), {
    target: { value: 'authored_work' },
  });
  await waitFor(() => expect(document.querySelector('.result-count')?.textContent).toBe('133'));
  await done();
  expect(document.querySelector('.query-panel').textContent).toContain('Auteur');
  await fireEvent.click(screen.getByRole('button', { name: '▦ Tableau' }));
  expect(screen.getByRole('table')).toBeTruthy();
  await fireEvent.click(screen.getByRole('button', { name: '◈ Constellation' }));
  expect(document.querySelector('.constellation-canvas')).toBeTruthy();
  await fireEvent.click(screen.getByLabelText('Revenir'));
  await waitFor(() => expect(document.querySelector('.result-count')?.textContent).toBe('132'));
  await done();
});
test('constellation recenters an entity and exposes bounded semantic groups', async () => {
  await ready();
  await fireEvent.click(screen.getByRole('button', { name: '◈ Constellation' }));
  expect(document.querySelector('.constellation-canvas')).toBeTruthy();
  const augustin = screen.getByRole('button', { name: 'Explorer Augustin d’Hippone' });
  await fireEvent.click(augustin);
  await waitFor(() => expect(document.querySelector('.constellation-center')?.textContent).toContain('Augustin'));
  await waitFor(() => expect(document.querySelectorAll('.constellation-node').length).toBeGreaterThan(0));
  expect(screen.getByLabelText('Nombre maximal de satellites')).toBeTruthy();
  const next = document.querySelector('.constellation-node.kind-group') || document.querySelector('.constellation-node');
  await fireEvent.click(next);
  await waitFor(() => expect(document.querySelector('.constellation-history-node')).not.toBeNull());
  expect(document.querySelector('.constellation-history-node').getAttribute('aria-label')).toContain('Augustin');
});
test('inspector applies reading policy and reveals sourced conflict only in research view', async () => {
  await ready();
  await fireEvent.click(screen.getByLabelText('Inspecter Augustin d’Hippone'));
  await waitFor(() =>
    expect(document.querySelectorAll('.assertion-card').length).toBeGreaterThan(0),
  );
  expect(document.querySelector('.status-pill.disputed')).toBeNull();
  const research = [...engine.policies.keys()][1];
  await fireEvent.change(screen.getByLabelText('Politique de lecture'), {
    target: { value: research },
  });
  await done();
  await fireEvent.click(screen.getByLabelText('Inspecter Augustin d’Hippone'));
  await waitFor(() => expect(document.querySelector('.status-pill.disputed')).not.toBeNull());
});
test('period, saved exploration, restoration and page cursor work', async () => {
  await ready();
  await fireEvent.input(screen.getByLabelText('Année de début'), { target: { value: '300' } });
  await fireEvent.input(screen.getByLabelText('Année de fin'), { target: { value: '500' } });
  await fireEvent.click(screen.getByRole('button', { name: 'Appliquer la période →' }));
  await done();
  expect(document.querySelector('.active-filters').textContent).toContain('300–500');
  const count = document.querySelector('.result-count').textContent;
  await fireEvent.click(screen.getByRole('button', { name: '＋ Enregistrer' }));
  await fireEvent.input(screen.getByLabelText('Nom de l’exploration'), {
    target: { value: 'Mes idées' },
  });
  await fireEvent.click(screen.getByRole('button', { name: 'Enregistrer ici' }));
  expect(JSON.parse(localStorage.getItem('konstellation.saved.v1'))[0].name).toBe('Mes idées');
  await fireEvent.click(screen.getByRole('button', { name: 'Réinitialiser' }));
  await done();
  expect(document.querySelector('.result-count').textContent).toBe('132');
  await fireEvent.click(screen.getByRole('button', { name: /^Mes idées/ }));
  await waitFor(() => expect(document.querySelector('.result-count').textContent).toBe(count));
  await done();
  await fireEvent.click(screen.getByRole('button', { name: 'Réinitialiser' }));
  await done();
  await fireEvent.click(screen.getByRole('button', { name: 'Suivante →' }));
  await done();
  expect(document.querySelector('.entity-list').textContent).not.toContain('Augustin d’Hippone');
});
test('communication exports real structured criteria and clears them when the exploration changes', async () => {
  await ready();
  await fireEvent.click(screen.getByText('Expliquer cette exploration'));
  await fireEvent.click(screen.getByRole('button', { name: 'Préparer la requête' }));
  await waitFor(() =>
    expect(screen.getByRole('button', { name: 'Exporter CommunicationRequest' })).toBeTruthy(),
  );
  expect(document.querySelector('.communication pre').textContent).toContain(
    'konstellation:selection-type',
  );
  expect(screen.getByRole('button', { name: 'Formuler avec SA' }).disabled).toBe(true);
  await fireEvent.click(screen.getByRole('checkbox', { name: /Philosophie/ }));
  await done();
  expect(screen.queryByRole('button', { name: 'Exporter CommunicationRequest' })).toBeNull();
});
test('unavailable facet capabilities display the cause without offering a false absence filter', async () => {
  engine.pack.integration = {
    capabilities: {
      relations: {
        field_of_work: {
          available: false,
          operators: [],
          reason: 'Relation indisponible dans ce pack.',
        },
      },
    },
  };
  await ready();
  expect(screen.getByText('Relation indisponible dans ce pack.')).toBeTruthy();
  expect(screen.queryByRole('checkbox', { name: /Philosophie/ })).toBeNull();
});
