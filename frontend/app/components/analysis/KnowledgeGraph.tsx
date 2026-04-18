"use client";
import { Search } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/app/components/ui/dialog";
import type { KnowledgeGraph as KGType } from "@/app/lib/types";

interface Props {
  graph: KGType | null;
  className?: string;
}

export function KnowledgeGraph({ graph, className }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (!graph || !svgRef.current) return;

    let cancelled = false;

    import("d3").then((d3) => {
      if (cancelled || !svgRef.current) return;

      const svg = d3.select(svgRef.current);
      svg.selectAll("*").remove();

      const el = svgRef.current;
      const width = el.clientWidth || 800;
      const height = el.clientHeight || 500;

      type NodeDatum = {
        id: string;
        label: string;
        type: string;
        color: string;
        x?: number;
        y?: number;
        vx?: number;
        vy?: number;
        fx?: number | null;
        fy?: number | null;
      };

      type LinkDatum = {
        source: string | NodeDatum;
        target: string | NodeDatum;
        relation: string;
      };

      const nodes: NodeDatum[] = graph.nodes.map((n) => ({ ...n }));
      const links: LinkDatum[] = graph.edges.map((e) => ({
        source: e.source,
        target: e.target,
        relation: e.relation,
      }));

      const sim = d3
        .forceSimulation<NodeDatum>(nodes)
        .force(
          "link",
          d3
            .forceLink<NodeDatum, LinkDatum>(links)
            .id((d) => d.id)
            .distance(120)
        )
        .force("charge", d3.forceManyBody().strength(-400))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collision", d3.forceCollide().radius(40));

      const container = svg.append("g");

      const zoom = d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.1, 8])
        .on("zoom", (event) => {
          container.attr("transform", event.transform);
        });

      svg.call(zoom);

      const link = container
        .append("g")
        .selectAll<SVGLineElement, LinkDatum>("line")
        .data(links)
        .join("line")
        .attr("stroke", "var(--border)")
        .attr("stroke-width", 1)
        .attr("opacity", 0.6);

      const linkLabel = container
        .append("g")
        .selectAll<SVGTextElement, LinkDatum>("text")
        .data(links)
        .join("text")
        .attr("font-size", "7px")
        .attr("fill", "var(--muted-foreground)")
        .attr("text-anchor", "middle")
        .attr("pointer-events", "none")
        .text((d) => d.relation);

      const node = container
        .append("g")
        .selectAll<SVGCircleElement, NodeDatum>("circle")
        .data(nodes)
        .join("circle")
        .attr("r", 16)
        .attr("fill", (d) => d.color || "var(--primary)")
        .attr("stroke", "white")
        .attr("stroke-width", 2)
        .attr("cursor", "grab")
        .call(
          d3
            .drag<SVGCircleElement, NodeDatum>()
            .on("start", (event, d) => {
              if (!event.active) sim.alphaTarget(0.3).restart();
              d.fx = d.x;
              d.fy = d.y;
            })
            .on("drag", (event, d) => {
              d.fx = event.x;
              d.fy = event.y;
              sim.restart();
            })
            .on("end", (event, d) => {
              if (!event.active) sim.alphaTarget(0);
              d.fx = null;
              d.fy = null;
            })
        );

      const label = container
        .append("g")
        .selectAll<SVGTextElement, NodeDatum>("text")
        .data(nodes)
        .join("text")
        .attr("font-size", "10px")
        .attr("text-anchor", "middle")
        .attr("dy", ".35em")
        .attr("fill", "var(--foreground)")
        .attr("pointer-events", "none")
        .attr("font-weight", "500")
        .text((d) => (d.label?.length > 10 ? d.label.slice(0, 8) + ".." : d.label));

      sim.on("tick", () => {
        link
          .attr("x1", (d) => (d.source as NodeDatum).x ?? 0)
          .attr("y1", (d) => (d.source as NodeDatum).y ?? 0)
          .attr("x2", (d) => (d.target as NodeDatum).x ?? 0)
          .attr("y2", (d) => (d.target as NodeDatum).y ?? 0);

        linkLabel
          .attr(
            "x",
            (d) => (((d.source as NodeDatum).x ?? 0) + ((d.target as NodeDatum).x ?? 0)) / 2
          )
          .attr(
            "y",
            (d) => (((d.source as NodeDatum).y ?? 0) + ((d.target as NodeDatum).y ?? 0)) / 2
          );

        node.attr("cx", (d) => d.x ?? 0).attr("cy", (d) => d.y ?? 0);
        label.attr("x", (d) => d.x ?? 0).attr("y", (d) => d.y ?? 0);
      });

      return () => {
        sim.stop();
      };
    });

    return () => {
      cancelled = true;
    };
  }, [graph, isOpen]);

  if (!graph) {
    return (
      <div className="text-sm text-[var(--muted-foreground)] p-4 text-center">
        No knowledge graph available.
      </div>
    );
  }

  return (
    <div className={`relative group ${className || ""}`}>
      <svg ref={svgRef} className="w-full h-80 rounded-xl border border-[var(--border)] bg-[var(--card)]" />
      
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="absolute top-3 right-3 p-2 rounded-lg bg-black/50 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/70 flex items-center gap-1.5 text-xs font-medium"
      >
        <Search size={14} />
        Expand Graph
      </button>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-[95vw] w-[95vw] h-[92vh] max-h-[92vh] p-4 flex flex-col">
          <DialogClose onClose={() => setIsOpen(false)} />
          <DialogHeader className="mb-2">
            <DialogTitle>Knowledge Graph Deep-Dive</DialogTitle>
            <p className="text-xs text-[var(--muted-foreground)]">
              Interactive force-directed graph. Drag nodes to explore relationships.
            </p>
          </DialogHeader>
          <div className="flex-1 min-h-0 bg-[var(--muted)]/20 rounded-xl border border-[var(--border)] overflow-hidden">
            <svg 
              ref={svgRef} 
              className="w-full h-full" 
              viewBox="0 0 1200 800"
              preserveAspectRatio="xMidYMid meet"
            />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
