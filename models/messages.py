"""
Strictly typed Pydantic message models for Agent communication.
Eliminates 'vibecoded' raw dictionaries and ensures deterministic interfaces.
"""

from typing import List, Optional, Any, Dict
from pydantic.v1 import BaseModel, Field
from uagents import Model

# --- Compound Agent ---
class CompoundRequest(Model):
    molecule: str = Field(..., description="The name of the compound to look up.")

class CompoundResponse(Model):
    status: str
    error: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None

# --- Reaction Agent ---
class ReactionRequest(Model):
    mol1: str
    mol2: str

class ReactionResponse(Model):
    status: str
    error: Optional[str] = None
    report: Optional[Dict[str, Any]] = None

# --- Research Agent ---
class ResearchRequest(Model):
    target_class: Optional[str] = None
    similar_to: Optional[str] = None
    min_activity: Optional[float] = None
    min_selectivity: Optional[float] = None

class ResearchResponse(Model):
    status: str
    error: Optional[str] = None
    discovery: Optional[Dict[str, Any]] = None

# --- Analysis Agent ---
class AnalysisRequest(Model):
    discovery_data: Dict[str, Any]
    criterion: str = "activity_score"
    ascending: bool = False

class AnalysisResponse(Model):
    status: str
    error: Optional[str] = None
    analysis: Optional[Dict[str, Any]] = None

# --- Database Agent (PubChem) ---
class LookupRequest(Model):
    query: str

class LookupResponse(Model):
    status: str
    error: Optional[str] = None
    compound: Optional[Dict[str, Any]] = None

# --- LLM Agent ---
class LLMInsightRequest(Model):
    context_type: str
    data: Dict[str, Any]

class LLMInsightResponse(Model):
    status: str
    error: Optional[str] = None
    insight: Optional[str] = None

class LLMGenerateRequest(Model):
    base_molecule: str

class LLMGenerateResponse(Model):
    status: str
    error: Optional[str] = None
    candidates: Optional[List[Dict[str, Any]]] = None
    is_available: bool = False

# --- Feedback Agent ---
class FeedbackLogRequest(Model):
    payload: Dict[str, Any]

class FeedbackLogResponse(Model):
    status: str
    error: Optional[str] = None
    entry: Optional[Dict[str, Any]] = None

class FeedbackGetLogsRequest(Model):
    pass

class FeedbackGetLogsResponse(Model):
    status: str
    error: Optional[str] = None
    logs: Optional[List[Dict[str, Any]]] = None
