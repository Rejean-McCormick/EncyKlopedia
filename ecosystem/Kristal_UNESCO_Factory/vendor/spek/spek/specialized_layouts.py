"""Explicit IDs and display groups for Spek specialized editorial renderers.

No content classification here: layout ID is always supplied in article.sections[]
by an upstream editorial selection. Visual grouping has no evidential authority.
"""
from __future__ import annotations

SPECIALIZED_FAMILIES = {
 'agroecosystem-network':'network','boundary-relation-map':'network','crossscale-distinctions-map':'network',
 'double-entry-ledger':'ledger','event-document-chain':'chain','evidence-constraint-matrix':'matrix',
 'functional-trajectory-map':'trajectory','inputs-practices-matrix':'matrix','mission-phase-map':'chain',
 'multiscale-relations-map':'network','period-rollup-matrix':'matrix','practice-interface-map':'network',
 'process-interface-map':'chain','relation-network':'network','source-provenance-index':'provenance',
 'stage-interaction-network':'network','system-interface-map':'network','taxonomy-tree':'taxonomy',
 'trajectory-constraints-map':'trajectory',
}

SPECIALIZED_SLOT_ORDER = {
 'network': ('context','entities','relations','limits'),
 'chain': ('context','stages','links','limits'),
 'matrix': ('context','axes','entries','limits'),
 'ledger': ('period_context','accounts','entries','reconciliations','limits'),
 'taxonomy': ('scope','concepts','specializations','limits'),
 'trajectory': ('context','observations','constraints','limits'),
 'provenance': ('context','sources','attributions','limits'),
}
