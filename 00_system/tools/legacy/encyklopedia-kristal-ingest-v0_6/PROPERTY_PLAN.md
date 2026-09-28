# Relation plan — people first

## Person anchors

- `P31` instance of
- `P19` place of birth
- `P20` place of death
- `P27` country of citizenship
- `P106` occupation
- `P101` field of work
- `P135` movement
- `P1142` political ideology
- `P737` influenced by
- `P69` educated at
- `P108` employer
- `P463` member of
- `P140` religion/worldview context

## Works / documents

Primary discovery:

- reverse `P50`: find items whose author is the seed person;
- direct `P800`: notable work attached to the person.

Optional later expansion:

- reverse `P170`: creator, useful beyond written works.

Work context retained when entity-valued:

- `P31`, `P50`, `P170`, `P136`, `P921`, `P407`, `P135`, `P361`, `P123`, `P629`, `P747`, `P144`.

`P577` and `P1476` are presently relation-presence markers only because generic literal values are not stored in the compact index.

## Intellectual currents

- `P135` movement — literary/artistic/scientific/philosophical movement.
- `P1142` political ideology — kept distinct from `P135`.
- `P101` field of work — exported separately as domain.
- `P737` influenced by — direct and reverse edges are kept with direction.

Absence of a Wikidata relation is treated as **absence from this source**, never proof that the relation does not exist historically.
