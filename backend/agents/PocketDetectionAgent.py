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
        mutant_pocket = None
        wt_pocket = None
        pocket_detection_method = None

        mutant_pdb_path = self._get_mutant_pdb_path(structures)
        wt_pdb_path = self._get_wt_pdb_path(state, structures)

        known = self._check_known_sites(structures)
        if known:
            pocket_detection_method = "known_site"
            binding_pocket = {**known, "method": "known_site"}
        else:
            binding_pocket = None

        if shutil.which("fpocket") and mutant_pdb_path:
            mutant_pocket = self._run_fpocket(mutant_pdb_path)
            if binding_pocket is None and mutant_pocket:
                pocket_detection_method = "fpocket"
                binding_pocket = {**mutant_pocket, "method": "fpocket"}
            if wt_pdb_path:
                wt_pocket = self._run_fpocket(wt_pdb_path)

        if binding_pocket is None and pdb_content:
            centroid = self._centroid_fallback(pdb_content)
            pocket_detection_method = "centroid"
            binding_pocket = {**centroid, "method": "centroid"}

        if binding_pocket is None:
            pocket_detection_method = "default"
            binding_pocket = {
                "center_x": 0.0,
                "center_y": 0.0,
                "center_z": 0.0,
                "size_x": 20,
                "size_y": 20,
                "size_z": 20,
                "score": 0.0,
                "method": "default",
            }

        result = {
            "binding_pocket": binding_pocket,
            "pocket_detection_method": pocket_detection_method or "unknown",
        }

        pocket_delta = self._build_pocket_delta(mutant_pocket, wt_pocket)
        if pocket_delta:
            result["pocket_delta"] = pocket_delta

        return result

    def _get_mutant_pdb_path(self, structures: list) -> str | None:
        for struct in structures:
            if struct.get("is_mutant") and struct.get("pdb_path"):
                return struct.get("pdb_path")
        for struct in structures:
            if struct.get("pdb_path"):
                return struct.get("pdb_path")
        return None

    def _get_wt_pdb_path(self, state: dict, structures: list) -> str | None:
        wt_path = state.get("wt_pdb_path")
        if wt_path:
            return wt_path
        for struct in structures:
            if struct.get("is_wildtype") and struct.get("pdb_path"):
                return struct.get("pdb_path")
        return None

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
        return {
            "center_x": 0.0,
            "center_y": 0.0,
            "center_z": 0.0,
            "size_x": 20,
            "size_y": 20,
            "size_z": 20,
            "score": 0.0,
        }
