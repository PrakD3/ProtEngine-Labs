"""Variant effect prediction using ESM-1v scores and mutation consequence analysis."""

import json
import re
from pathlib import Path
from typing import Literal

MUTATION_RESISTANCE_PATH = Path(__file__).parent.parent / "data" / "mutation_resistance.json"


class VariantEffectAgent:
    """Reads mutation_context, proteins; writes esm1v_score, esm1v_confidence."""

    async def run(self, state: dict) -> dict:
        from utils.logger import get_logger

        log = get_logger(self.__class__.__name__)
        log.info("starting")
        try:
            result = await self._execute(state)
            log.info("complete")
            return result
        except Exception as exc:
            log.error("failed", exc_info=True)
            return {"errors": [f"VariantEffectAgent failed: {exc}"]}

    async def _execute(self, state: dict) -> dict:
        plan = state.get("analysis_plan")
        if not getattr(plan, "run_structure", True):
            return {}

        mutation_context = state.get("mutation_context", {})
        proteins = state.get("proteins", [])
        query = state.get("query", "")

        gene = mutation_context.get("gene", "")
        mutation = mutation_context.get("mutation", "")

        # Try to get known scores from database
        known_score = self._lookup_known_mutation(gene, mutation, query)
        if known_score:
            return {
                "esm1v_score": known_score["score"],
                "esm1v_confidence": known_score["confidence"],
                "esm1v_method": "known_database",
                "variant_consequence": known_score["consequence"],
            }

        # Fallback: infer from mutation type + protein conservation
        consequence = self._classify_consequence(mutation)
        score, confidence = self._predict_pathogenicity(
            mutation, consequence, proteins, gene
        )

        return {
            "esm1v_score": score,
            "esm1v_confidence": confidence,
            "esm1v_method": "conservation_based",
            "variant_consequence": consequence,
        }

    def _lookup_known_mutation(
        self, gene: str, mutation: str, query: str
    ) -> dict | None:
        """Check mutation_resistance.json for known mutations."""
        try:
            with open(MUTATION_RESISTANCE_PATH) as f:
                data = json.load(f)
        except Exception:
            return None

        key = f"{gene} {mutation}".strip()
        if key in data:
            entry = data[key]
            # Determine pathogenicity from resistance data
            is_resistant = len(entry.get("resistant_to", [])) > 0
            score = 0.85 if is_resistant else 0.65  # High score = pathogenic
            confidence = "PATHOGENIC" if is_resistant else "UNCERTAIN"
            # Infer consequence from mutation string or mechanism
            consequence = self._classify_consequence(mutation)
            return {
                "score": score,
                "confidence": confidence,
                "consequence": consequence,
            }

        # Also check lowercase
        key_lower = key.lower()
        for k, v in data.items():
            if k.lower() == key_lower:
                is_resistant = len(v.get("resistant_to", [])) > 0
                score = 0.85 if is_resistant else 0.65
                confidence = "PATHOGENIC" if is_resistant else "UNCERTAIN"
                consequence = self._classify_consequence(mutation)
                return {
                    "score": score,
                    "confidence": confidence,
                    "consequence": consequence,
                }

        return None

    def _classify_consequence(self, mutation: str) -> str:
        """Classify mutation consequence from mutation string."""
        mutation = mutation.upper().strip()

        # Frameshift: insertions/deletions with numbers
        if "INS" in mutation or "DEL" in mutation:
            return "frameshift_variant"

        # Stop gain: *nn (nonsense)
        if "*" in mutation or "STOP" in mutation or "TER" in mutation:
            return "stop_gained"

        # Splice site: splice region mutations
        if "SPLICE" in mutation or mutation.startswith("+") or mutation.startswith("-"):
            return "splice_site_variant"

        # Missense: [A-Z]\d+[A-Z] pattern
        missense_pattern = r"^[A-Z]\d+[A-Z*]"
        if re.match(missense_pattern, mutation):
            return "missense_variant"

        # Inframe indel
        if ("INS" in mutation or "DEL" in mutation) and ("3" in mutation or "6" in mutation):
            return "inframe_indel"

        # Default
        return "sequence_variant"

    def _predict_pathogenicity(
        self, mutation: str, consequence: str, proteins: list, gene: str
    ) -> tuple[float, Literal["PATHOGENIC", "UNCERTAIN", "BENIGN"]]:
        """
        Predict pathogenicity score based on consequence type and protein data.
        
        Returns:
            score (0-1): Higher = more pathogenic. Would be replaced with real ESM-1v model.
            confidence: PATHOGENIC | UNCERTAIN | BENIGN
        
        NOTE: This uses heuristics. In production, replace with:
        - Fair-ESM library (facebook/esm) for ESM-1v variant effect prediction
        - Or call ESMvep API if available
        """

        # Consequence-based scoring (heuristic)
        consequence_scores = {
            "stop_gained": 0.95,  # Very likely pathogenic
            "frameshift_variant": 0.90,  # Very likely pathogenic
            "splice_site_variant": 0.88,  # Very likely pathogenic
            "missense_variant": 0.55,  # Variable - depends on residue
            "inframe_indel": 0.65,  # Likely pathogenic
            "sequence_variant": 0.40,  # Uncertain
        }

        base_score = consequence_scores.get(consequence, 0.40)

        # Adjust based on protein conservation (if available)
        if proteins:
            conservation = self._estimate_conservation(mutation, proteins)
            base_score = base_score * 0.7 + conservation * 0.3

        # Confidence thresholds
        if base_score >= 0.75:
            confidence = "PATHOGENIC"
        elif base_score >= 0.50:
            confidence = "UNCERTAIN"
        else:
            confidence = "BENIGN"

        return round(base_score, 2), confidence

    def _estimate_conservation(self, mutation: str, proteins: list) -> float:
        """Estimate conservation score from available protein alignment data."""
        if not proteins:
            return 0.5

        # Extract position from mutation
        pos_match = re.search(r"\d+", mutation)
        if not pos_match:
            return 0.5

        position = int(pos_match.group())

        # Look for conservation info in protein sequences
        conservation_score = 0.5
        for protein in proteins:
            # If we have sequence info, could compute MSA conservation
            # For now, return neutral score
            if isinstance(protein, dict) and "sequence" in protein:
                seq_len = len(protein.get("sequence", ""))
                if seq_len > 0 and position <= seq_len:
                    conservation_score = 0.6  # Slight boost if position is in sequence

        return conservation_score
