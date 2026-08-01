"""
BioAgents Domain Model
=======================
All shared immutable value objects that flow between layers.

Design decisions
----------------
- Plain ``@dataclass`` (not Pydantic) to keep the dependency surface minimal
  and avoid validation magic that obscures intent.
- ``dataclasses.asdict()`` provides recursive JSON-serialisable conversion.
- No business logic lives here — these are pure data containers.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Core vocabulary
# ---------------------------------------------------------------------------

@dataclass
class DrugInteraction:
    """A known adverse interaction between two named compounds."""
    drug: str          # the *other* compound in the pair
    effect: str        # pharmacological effect label (underscore-separated)
    severity: str      # raw severity token: "low" | "moderate" | "high"

    @property
    def severity_rank(self) -> int:
        """Numeric severity for comparison: high=3, moderate=2, low=1, unknown=0."""
        return {"high": 3, "moderate": 2, "low": 1}.get(self.severity.lower(), 0)


@dataclass
class MoleculeProperties:
    """All computable properties of a molecule drawn from the MeTTa knowledge base."""
    molecular_weight:  Optional[float]
    formula:           Optional[str]
    categories:        list[str]        # e.g. ["NSAID", "analgesic"]
    targets:           list[str]        # e.g. ["COX1", "COX2"]
    functional_groups: list[str]        # e.g. ["metal_oxide", "zeolite"]
    activity_score:    Optional[float]  # 0.0 → 1.0 (catalytic conversion efficiency / yield)
    selectivity:       Optional[float]  # 0.0 → 1.0 (specificity to desired product)
    stability_h:       Optional[float]  # hours of continuous operation before deactivation

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CompoundProfile:
    """Complete profile for a single molecule, including relational data."""
    molecule:           str
    properties:         MoleculeProperties
    similar_compounds:  list[str]
    known_interactions: list[DrugInteraction]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CandidateCompound:
    """A molecule matched by a discovery query plus its properties."""
    molecule:   str
    properties: MoleculeProperties

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class InteractionReport:
    """Full assessment of a drug–drug interaction pair."""
    compound_1:             str
    compound_2:             str
    targets_1:              list[str]
    targets_2:              list[str]
    shared_targets:         list[str]
    explicit_interactions:  list[DrugInteraction]
    risk_level:             str          # "Low" | "Moderate" | "High"
    warnings:               list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DiscoveryResult:
    """Result of a ResearchService.discover() call."""
    query:      dict[str, Any]
    count:      int
    candidates: list[CandidateCompound]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RankingStats:
    """Descriptive statistics over the ranked score distribution."""
    minimum: float
    maximum: float
    mean:    float
    median:  float


@dataclass
class RankedResult:
    """Result of an AnalysisService.rank() call."""
    criterion:         str
    sort_order:        str          # "ascending" | "descending"
    count:             int
    skipped:           list[str]   # molecules that lacked the criterion value
    stats:             RankingStats
    ranked_candidates: list[CandidateCompound]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PubChemCompound:
    """Properties fetched live from the NIH PubChem PUG REST API."""
    cid:               int
    iupac_name:        Optional[str]
    molecular_formula: Optional[str]
    molecular_weight:  Optional[float]
    isomeric_smiles:   Optional[str]
    xlogp:             Optional[float]
    charge:            Optional[int]
    synonyms:          list[str]
    connectivity_smiles: Optional[str] = None
    source_url: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KnowledgeGraphNode:
    id:       str
    group:    int           # integer colour group (by primary category)
    category: str
    val:      float         # visual size scales with activity_score


@dataclass
class KnowledgeGraphEdge:
    source:   str
    target:   str
    value:    int
    type:     str           # "similar" | "interaction"
    severity: Optional[str] = None


@dataclass
class KnowledgeGraph:
    nodes: list[KnowledgeGraphNode]
    links: list[KnowledgeGraphEdge]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
