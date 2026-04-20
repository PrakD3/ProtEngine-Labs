import { useEffect, useRef, useState } from "react";

interface Props {
  pdbId?: string;
  proteinUrl?: string;
  ligandPoseUrl?: string;
  ligandPoseFormat?: string | null;
  className?: string;
  lowQuality?: boolean;
  noSpin?: boolean;
}

export function MoleculeViewer3D({
  pdbId,
  proteinUrl,
  ligandPoseUrl,
  ligandPoseFormat,
  className,
  lowQuality = false,
  noSpin = false,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<any>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined" || !containerRef.current) return;

    let stage: any;

    import("ngl").then((NGL) => {
      if (!containerRef.current) return;
      setLoadError(null);

      // Standardize quality to ensure transparency is supported
      stage = new NGL.Stage(containerRef.current, {
        tooltip: !lowQuality,
        sampleLevel: 0, // 0 is the sweet spot for speed + transparency
      });

      // Low-level transparency fix: target the renderer and container
      if (stage.viewer.renderer) {
        stage.viewer.renderer.setClearAlpha(0.0);
        stage.viewer.renderer.setClearColor(0xffffff, 0); // Transparent white base
        
        const canvas = stage.viewer.renderer.domElement;
        if (canvas) {
          canvas.style.background = "transparent";
          canvas.style.backgroundColor = "transparent";
        }
      }

      if (stage.viewer.container) {
        stage.viewer.container.style.background = "transparent";
        stage.viewer.container.style.backgroundColor = "transparent";
      }
      
      stageRef.current = stage;

      // Global spin setting
      if (!noSpin) stage.setSpin(true);

      const loadAll = async () => {
        if (!stage || (!pdbId && !proteinUrl && !ligandPoseUrl)) return;
        
        let proteinComponent: any = null;
        let ligandComponent: any = null;

        try {
          // 1. Try refined protein from session structure
          if (proteinUrl) {
            proteinComponent = await stage.loadFile(proteinUrl, { ext: "pdb" });
          } 
          // 2. Fallback to generic PDB structure if refined not available
          else if (pdbId) {
            const pdbCode = pdbId.trim().toUpperCase();
            if (/^[0-9A-Z]{4}$/.test(pdbCode)) {
              const pdbUrl = `https://files.rcsb.org/download/${pdbCode}.pdb`;
              proteinComponent = await stage.loadFile(pdbUrl, { ext: "pdb" });
            }
          }

          if (proteinComponent) {
            proteinComponent.addRepresentation("cartoon", {
              color: "residueindex",
              opacity: 1.0,
              quality: lowQuality ? "low" : "high",
            });
          }
        } catch (e) {
          console.warn("NGL protein load failed:", e);
        }

        try {
          if (ligandPoseUrl) {
            const parts = ligandPoseUrl.split("/");
            const lastPart = parts[parts.length - 1];
            const inferredExt = lastPart.includes(".") ? lastPart.split(".").pop()?.toLowerCase() : null;
            
            // Smart fallback for API-served poses
            const ext = (ligandPoseFormat || inferredExt || "pdbqt").toLowerCase();
            ligandComponent = await stage.loadFile(ligandPoseUrl, { ext });
          }

          if (ligandComponent) {
            ligandComponent.addRepresentation("ball+stick", {
              color: "element",
              scale: 2.0,
              quality: lowQuality ? "low" : "high",
            });
          }
        } catch (e) {
             console.warn("NGL ligand load failed:", e);
        }

        if (ligandComponent) {
          ligandComponent.autoView();
        } else if (proteinComponent) {
          proteinComponent.autoView();
        } else {
          setLoadError("Structure unavailable.");
        }
      };

      void loadAll();
    });

    return () => {
      if (stage) {
        stage.dispose();
      }
      stageRef.current = null;
    };
  }, [pdbId, proteinUrl, ligandPoseUrl, ligandPoseFormat, lowQuality, noSpin]);

  return (
    <div
      ref={containerRef}
      className={`w-full rounded border border-primary/20 bg-transparent relative overflow-hidden ${className ?? "h-64"}`}
    >
      {(!pdbId && !proteinUrl && !ligandPoseUrl) && (
        <div className="absolute inset-0 flex items-center justify-center text-[10px] text-[var(--muted-foreground)]">
          Waiting for structural data...
        </div>
      )}
      {loadError && (
        <div className="absolute inset-0 flex items-center justify-center text-[10px] text-red-400">
          {loadError}
        </div>
      )}
    </div>
  );
}
