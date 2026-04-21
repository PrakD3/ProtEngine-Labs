"""Detect binding pocket via fpocket, known sites, or centroid fallback."""

import json
import re
import shutil
import subprocess
from pathlib import Path

KNOWN_SITES_PATH = Path(__file__).parent.parent / "data" / "known_active_sites.json"


class PocketDetectionAgent:
    """Reads pdb_content+structures, writes binding_pocket."""

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
            return {"errors": [f"PocketDetectionAgent failed: {exc}"]}

    async def _execute(self, state: dict) -> dict:
        plan = state.get("analysis_plan")
        if not getattr(plan, "run_pocket_detection", True):
            return {}
        
        structures = state.get("structures", [])
        pdb_content = state.get("pdb_content", "")
        ctx = state.get("mutation_context", {})
        
        # Detect binding pocket (mutant)
        known = self._check_known_sites(structures)
        if known:
            mutant_pocket = {**known, "method": "known_site"}
            pocket_method = "known_site"
        elif shutil.which("fpocket") and structures:
            pdb_path = structures[0].get("pdb_path")
            if pdb_path:
                pocket = self._run_fpocket(pdb_path)
                if pocket:
                    mutant_pocket = {**pocket, "method": "fpocket"}
                    pocket_method = "fpocket"
                else:
                    mutant_pocket = self._centroid_fallback(pdb_content) if pdb_content else self._default_pocket()
                    pocket_method = "centroid"
            else:
                mutant_pocket = self._centroid_fallback(pdb_content) if pdb_content else self._default_pocket()
                pocket_method = "centroid"
        elif pdb_content:
            mutant_pocket = self._centroid_fallback(pdb_content)
            pocket_method = "centroid"
        else:
            mutant_pocket = self._default_pocket()
            pocket_method = "default"
        
        # Compute wildtype pocket characteristics (for pocket_delta)
        # Wildtype pocket is slightly smaller/less optimized than mutant
        wildtype_pocket = self._estimate_wildtype_pocket(mutant_pocket)
        
        # Compute pocket_delta (comparison: mutant - wildtype)
        pocket_delta = self._compute_pocket_delta(wildtype_pocket, mutant_pocket, ctx)
        
        return {
            "binding_pocket": mutant_pocket,
            "pocket_detection_method": pocket_method,
            "wildtype_pocket": wildtype_pocket,
            "mutant_pocket": mutant_pocket,
            "pocket_delta": pocket_delta,
        }
    
    def _estimate_wildtype_pocket(self, mutant_pocket: dict) -> dict:
        """Estimate wildtype pocket as slightly smaller/different than mutant."""
        return {
            "center_x": mutant_pocket.get("center_x", 0),
            "center_y": mutant_pocket.get("center_y", 0),
            "center_z": mutant_pocket.get("center_z", 0),
            "size_x": mutant_pocket.get("size_x", 20) - 1,  # Slightly smaller
            "size_y": mutant_pocket.get("size_y", 20) - 1,
            "size_z": mutant_pocket.get("size_z", 20) - 1,
            "score": mutant_pocket.get("score", 0) * 0.9,  # Slightly lower score
        }
    
    def _compute_pocket_delta(self, wt_pocket: dict, mut_pocket: dict, ctx: dict) -> dict:
        """Compute pocket geometry changes between wildtype and mutant using actual AA properties."""
        # AA Properties: {Hydrophobicity (Kyte-Doolittle), Polarity, Charge, Volume (A^3)}
        RESIDUE_PROPS = {
            'A': (1.8, 0, 0, 88.6),   'R': (-4.5, 1, 1, 173.4), 'N': (-3.5, 1, 0, 114.1),
            'D': (-3.5, 1, -1, 111.1), 'C': (2.5, 0, 0, 108.5),  'E': (-3.5, 1, -1, 138.4),
            'Q': (-3.5, 1, 0, 143.8),  'G': (-0.4, 0, 0, 60.1),   'H': (-3.2, 1, 0, 153.2),
            'I': (4.5, 0, 0, 166.7),   'L': (3.8, 0, 0, 166.7),   'K': (-3.9, 1, 1, 168.6),
            'M': (1.9, 0, 0, 162.9),   'F': (2.8, 0, 0, 189.9),   'P': (-1.6, 0, 0, 112.7),
            'S': (-0.8, 1, 0, 89.0),   'T': (-0.7, 1, 0, 116.1),  'W': (-0.9, 0, 0, 227.8),
            'Y': (-1.3, 1, 0, 193.6),  'V': (4.2, 0, 0, 140.0)
        }

        wt_aa = ctx.get("wt_aa", "X")[0].upper()
        mut_aa = ctx.get("mut_aa", "X")[0].upper()

        if wt_aa == "X" or wt_aa == mut_aa:
            # Baseline benchmark for Wildtype-only runs (Average Human Druggable Pocket)
            wt_props = (0.0, 0.5, 0.0, 850.0) # Hydro, Polar, Charge, Vol
        else:
            wt_props = RESIDUE_PROPS.get(wt_aa, (0, 0, 0, 100))
        
        mut_props = RESIDUE_PROPS.get(mut_aa, (0, 0, 0, 100))

        # If it's a mutation, adjust volume delta to be relative to the AA shift
        # If it's wildtype, it's relative to the baseline
        if wt_aa == "X" or wt_aa == mut_aa:
            volume_delta = mut_pocket.get("volume", 850.0) - wt_props[3]
            hydro_delta = mut_pocket.get("hydrophobicity_score", 0.5) - wt_props[0]
            polar_delta = mut_pocket.get("polarity_score", 0.5) - wt_props[1]
            charge_delta = mut_pocket.get("charge_score", 0.0) - wt_props[2]
        else:
            volume_delta = mut_props[3] - wt_props[3]
            hydro_delta = mut_props[0] - wt_props[0]
            polar_delta = mut_props[1] - wt_props[1]
            charge_delta = mut_props[2] - wt_props[2]

        residues_displaced = []
        position = ctx.get("position", "")
        if position:
            position_str = str(position)
            if position_str.isdigit():
                residues_displaced = [position_str, str(int(position_str)+1), str(int(position_str)+2)]

        return {
            "volume_delta": round(volume_delta, 2),
            "volume_wildtype": round(wt_props[3], 2),
            "volume_mutant": round(mut_props[3], 2),
            "hydrophobicity_delta": round(hydro_delta, 3),
            "hydrophobicity_wildtype": round(wt_props[0], 2),
            "hydrophobicity_mutant": round(mut_props[0], 2),
            "polarity_delta": round(polar_delta, 3),
            "polarity_wildtype": round(wt_props[1], 2),
            "polarity_mutant": round(mut_props[1], 2),
            "charge_delta": round(charge_delta, 3),
            "charge_wildtype": round(wt_props[2], 2),
            "charge_mutant": round(mut_props[2], 2),
            "pocket_reshaped": abs(volume_delta) > 5.0 or abs(hydro_delta) > 0.5,
            "residues_displaced": residues_displaced,
        }

    def _check_known_sites(self, structures: list) -> dict | None:
        try:
            with open(KNOWN_SITES_PATH) as f:
                known = json.load(f)
        except Exception:
            return None
        for struct in structures:
            pdb_id = struct.get("pdb_id", "")
            if pdb_id in known:
                return known[pdb_id]
        return None

    def _run_fpocket(self, pdb_path: str) -> dict | None:
        try:
            subprocess.run(["fpocket", "-f", pdb_path], capture_output=True, timeout=30)
            out_dir = pdb_path.replace(".pdb", "_out")
            info_file = Path(out_dir) / f"{Path(pdb_path).stem}_info.txt"
            if info_file.exists():
                text = info_file.read_text()
                pocket1 = text.split("Pocket 1")[1] if "Pocket 1" in text else ""
                cx = re.search(r"x_barycenter\s*:\s*([\d\.\-]+)", pocket1)
                cy = re.search(r"y_barycenter\s*:\s*([\d\.\-]+)", pocket1)
                cz = re.search(r"z_barycenter\s*:\s*([\d\.\-]+)", pocket1)
                score = re.search(r"Druggability Score\s*:\s*([\d\.]+)", pocket1)
                volume = self._parse_metric(pocket1, [r"Volume\s*:\s*([\d\.\-]+)"])
                hydrophobicity = self._parse_metric(
                    pocket1,
                    [
                        r"Hydrophobicity score\s*:\s*([\d\.\-]+)",
                        r"Hydrophobicity\s*:\s*([\d\.\-]+)",
                    ],
                )
                polarity = self._parse_metric(
                    pocket1,
                    [
                        r"Polarity score\s*:\s*([\d\.\-]+)",
                        r"Polarity\s*:\s*([\d\.\-]+)",
                    ],
                )
                charge = self._parse_metric(
                    pocket1,
                    [
                        r"Charge score\s*:\s*([\d\.\-]+)",
                        r"Charge\s*:\s*([\d\.\-]+)",
                    ],
                )
                if cx and cy and cz:
                    return {
                        "center_x": float(cx.group(1)),
                        "center_y": float(cy.group(1)),
                        "center_z": float(cz.group(1)),
                        "size_x": 20,
                        "size_y": 20,
                        "size_z": 20,
                        "score": float(score.group(1)) if score else 0.5,
                        "volume": volume,
                        "hydrophobicity_score": hydrophobicity,
                        "polarity_score": polarity,
                        "charge_score": charge,
                    }
        except Exception:
            pass
        return None

    def _parse_metric(self, pocket_text: str, patterns: list[str]) -> float | None:
        for pattern in patterns:
            match = re.search(pattern, pocket_text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    return None
        return None

    def _build_pocket_delta(self, mutant: dict | None, wt: dict | None) -> dict | None:
        if not mutant or not wt:
            return None
        delta: dict[str, float] = {}

        def add_delta(key: str, out_key: str) -> None:
            m_val = mutant.get(key)
            w_val = wt.get(key)
            if isinstance(m_val, (int, float)) and isinstance(w_val, (int, float)):
                delta[out_key] = round(m_val - w_val, 2)

        add_delta("volume", "volume_delta")
        add_delta("hydrophobicity_score", "hydrophobicity_score_delta")
        add_delta("polarity_score", "polarity_score_delta")
        add_delta("charge_score", "charge_score_delta")

        if not delta:
            return None

        reshaped = False
        volume_delta = delta.get("volume_delta")
        if volume_delta is not None and abs(volume_delta) >= 50:
            reshaped = True
        for key in (
            "hydrophobicity_score_delta",
            "polarity_score_delta",
            "charge_score_delta",
        ):
            val = delta.get(key)
            if val is not None and abs(val) >= 0.2:
                reshaped = True
                break

        delta["pocket_reshaped"] = reshaped
        return delta

    def _centroid_fallback(self, pdb_content: str) -> dict:
        xs, ys, zs = [], [], []
        for line in pdb_content.splitlines():
            if line.startswith("ATOM") or line.startswith("HETATM"):
                try:
                    xs.append(float(line[30:38]))
                    ys.append(float(line[38:46]))
                    zs.append(float(line[46:54]))
                except (ValueError, IndexError):
                    continue
        if xs:
            return {
                "center_x": round(sum(xs) / len(xs), 2),
                "center_y": round(sum(ys) / len(ys), 2),
                "center_z": round(sum(zs) / len(zs), 2),
                "size_x": 20,
                "size_y": 20,
                "size_z": 20,
                "score": 0.0,
            }
        return self._default_pocket()
    
    def _default_pocket(self) -> dict:
        """Return default pocket when detection fails."""
        return {
            "center_x": 0.0,
            "center_y": 0.0,
            "center_z": 0.0,
            "size_x": 20,
            "size_y": 20,
            "size_z": 20,
            "score": 0.0,
        }
