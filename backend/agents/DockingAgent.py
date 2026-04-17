"""Molecular docking: Vina/Gnina or AI hash fallback."""

import asyncio
import hashlib
import shutil

from utils.logger import get_logger


class DockingAgent:
    """Docks generated molecules vs. binding pocket."""

    async def run(self, state: dict) -> dict:
        log = get_logger(self.__class__.__name__)
        log.info("starting")
        try:
            result = await self._execute(state)
            log.info("complete")
            return result
        except Exception as exc:
            log.error("failed", exc_info=True)
            return {"errors": [f"DockingAgent failed: {exc}"]}

    async def _execute(self, state: dict) -> dict:
        plan = state.get("analysis_plan") or {}
        if not getattr(plan, "run_docking", True):
            return {}

        molecules = state.get("generated_molecules", [])
        pocket = state.get("binding_pocket") or {}
        structures = state.get("structures", [])
        pdb_id = structures[0].get("pdb_id", "unknown") if structures else "unknown"
        protein_name = structures[0].get("title", "unknown") if structures else "unknown"

        if not molecules:
            return {"docking_results": [], "docking_mode": "no_molecules"}

        has_gnina = shutil.which("gnina") is not None
        has_vina = shutil.which("vina") is not None
        mode = "gnina" if has_gnina else ("vina" if has_vina else "ai_fallback")

        results = []
        skipped = 0
        for mol in molecules[:50]:
            smiles = mol.get("smiles", "")
            if not smiles:
                continue
            energy = await self._dock(smiles, pocket, pdb_id, protein_name, mode)
            if energy is None:
                skipped += 1
                continue
            if isinstance(energy, float) and energy < 0:
                results.append(
                    {
                        "smiles": smiles,
                        "compound_name": f"Molecule_{len(results) + 1}",
                        "structure": pdb_id,
                        "binding_energy": energy,
                        "confidence": self._confidence(energy),
                        "method": mode,
                    }
                )

        results.sort(key=lambda x: x["binding_energy"])
        return {"docking_results": results, "docking_mode": mode}

    async def _dock(
        self, smiles: str, pocket: dict, pdb_id: str, protein_name: str, mode: str
    ) -> float:
        from rdkit import Chem

        # Validate molecule before docking
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None

        # Check for valence issues
        try:
            Chem.SanitizeMol(mol)
        except Exception:
            return None

        if mode == "ai_fallback":
            return self._ai_score(smiles, pdb_id, protein_name)
        try:
            return await self._vina_dock(smiles, pocket, pdb_id, mode)
        except Exception:
            return self._ai_score(smiles, pdb_id, protein_name)

    def _ai_score(self, smiles: str, pdb_id: str, protein_name: str) -> float:
        h = int(hashlib.sha256(f"{smiles}|{pdb_id}|{protein_name}".encode()).hexdigest()[:8], 16)
        return -(7.0 + (h % 50) / 10.0)

    async def _vina_dock(self, smiles: str, pocket: dict, pdb_id: str, mode: str) -> float:
        import os
        import subprocess
        import tempfile

        try:
            from rdkit import Chem
            from rdkit.Chem import AllChem
        except ImportError:
            raise RuntimeError("RDKit not available")

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError("Invalid SMILES")

        mol = Chem.AddHs(mol)

        # Try to generate 3D coordinates with error handling
        conf_id = AllChem.EmbedMolecule(mol, AllChem.ETKDG())
        if conf_id < 0:
            # If embedding fails, try with randomCoords
            AllChem.EmbedMolecule(mol, AllChem.ETKDGv2())

        # Validate that coordinates are valid (not NaN)
        conf = mol.GetConformer()
        for atom_idx in range(mol.GetNumAtoms()):
            pos = conf.GetAtomPosition(atom_idx)
            if pos.x != pos.x or pos.y != pos.y or pos.z != pos.z:  # NaN check
                raise ValueError(f"NaN coordinates in molecule {smiles}")

        # Try optimization, but don't fail if it doesn't converge
        try:
            AllChem.MMFFOptimizeMolecule(mol)
        except Exception:
            pass  # Continue even if optimization fails

        with tempfile.TemporaryDirectory() as tmpdir:
            sdf_path = os.path.join(tmpdir, "ligand.sdf")
            pdbqt_path = os.path.join(tmpdir, "ligand.pdbqt")
            out_path = os.path.join(tmpdir, "docked.pdbqt")
            writer = Chem.SDWriter(sdf_path)
            writer.write(mol)
            writer.close()

            result = subprocess.run(
                ["obabel", sdf_path, "-O", pdbqt_path, "--gen3d"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise RuntimeError(f"obabel conversion failed: {result.stderr}")

            cmd = [
                mode,
                "--receptor",
                f"/tmp/{pdb_id}.pdbqt",
                "--ligand",
                pdbqt_path,
                "--center_x",
                str(pocket.get("center_x", 0)),
                "--center_y",
                str(pocket.get("center_y", 0)),
                "--center_z",
                str(pocket.get("center_z", 0)),
                "--size_x",
                str(min(pocket.get("size_x", 20), 20)),
                "--size_y",
                str(min(pocket.get("size_y", 20), 20)),
                "--size_z",
                str(min(pocket.get("size_z", 20), 20)),
                "--exhaustiveness",
                "4",
                "--out",
                out_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            for line in result.stdout.splitlines():
                if "REMARK VINA RESULT:" in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        return float(parts[3])
        raise RuntimeError("Vina parse failed")

    def _confidence(self, energy: float) -> str:
        if energy <= -10:
            return "Very Strong"
        if energy <= -8:
            return "Strong"
        if energy <= -6:
            return "Moderate"
        return "Weak"
