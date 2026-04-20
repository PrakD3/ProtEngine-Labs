"use client";

import { useEffect, useState } from "react";
import { Matrix } from "@/components/unlumen-ui/matrix";
import { MoleculeViewer3D } from "./MoleculeViewer3D";
import { PipelineState } from "@/app/lib/types";

interface Props {
  sessionId: string;
  latestState: Partial<PipelineState> | null;
  currentAgent: string | undefined;
  progress: number;
  matrixLevels: number[];
}

export function LiveSimulationView({
  sessionId,
  latestState,
  currentAgent,
  progress,
  matrixLevels,
}: Props) {
  const [pdbBlobUrl, setPdbBlobUrl] = useState<string | null>(null);

  // Agent check for simulation stages
  const isStructureLoaded = !!latestState?.pdb_content;
  const earlyPdbId = latestState?.structures?.[0]?.pdb_id;
  const isDocking = currentAgent?.toLowerCase().includes("docking") || !!latestState?.docking_results?.length;

  // We show 3D if we have content OR a valid ID to fetch from RCSB
  const show3D = isStructureLoaded || !!earlyPdbId;

  useEffect(() => {
    if (isStructureLoaded && latestState?.pdb_content) {
      const blob = new Blob([latestState.pdb_content], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      setPdbBlobUrl(url);

      return () => {
        URL.revokeObjectURL(url);
      };
    }
  }, [isStructureLoaded, latestState?.pdb_content]);

  return (
    <div className="w-full relative min-h-[400px] flex flex-col items-center justify-center">
      {/* Abstract Grid View (Initial) */}
      {!show3D && (
        <div className="flex flex-col items-center gap-8 animate-in fade-in duration-700">
          <Matrix
            rows={10}
            cols={52}
            mode="vu"
            levels={matrixLevels}
            fps={14}
            size={17}
            gap={5}
            palette={{
              on: "var(--primary)",
              off: "var(--border)",
            }}
            className="text-[var(--primary)] opacity-60"
          />
          <p className="text-[10px] font-mono uppercase tracking-widest text-[var(--muted-foreground)] animate-pulse">
             Orchestrating Agents & Sourcing Data...
          </p>
        </div>
      )}

      {/* 3D Simulation View (Live Bio-data) */}
      {show3D && (
        <div className="w-full h-[500px] animate-in zoom-in-95 fade-in duration-1000 relative">
          <MoleculeViewer3D 
            proteinUrl={pdbBlobUrl || undefined}
            pdbId={!pdbBlobUrl ? earlyPdbId : undefined}
            className="h-full rounded-2xl border-2 border-primary/5 shadow-2xl shadow-primary/5"
          />
          
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-2/3 h-1 bg-white/5 rounded-full overflow-hidden">
             <div 
               className="h-full bg-primary transition-all duration-500" 
               style={{ width: `${progress}%` }} 
             />
          </div>
          
          <div className="mt-4 text-center">
             <p className="text-xs font-medium text-[var(--muted-foreground)]">
                {isDocking 
                  ? "Computational ligand-pose optimization in progress..." 
                  : isStructureLoaded 
                    ? "Bio-physical refinement of binding pocket complete." 
                    : "Fetching initial structural coordinates from global repository..."}
             </p>
          </div>
        </div>
      )}
    </div>
  );
}
