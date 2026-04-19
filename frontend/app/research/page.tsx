"use client";

import {
  ArrowRight,
  Dna,
  Loader2,
  Search,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useAnalysis } from "@/app/hooks/useAnalysis";
import { searchMutations } from "@/app/lib/api";

const DEMO_CHIPS = ["EGFR T790M", "HIV K103N", "BRCA1 5382insC", "TP53 R248W"];



export default function ResearchPage() {
  const router = useRouter();
  const { launch, isLoading } = useAnalysis();
  const [query, setQuery] = useState("");
  const [localSuggestions, setLocalSuggestions] = useState<string[]>([]);
  const [onlineSuggestions, setOnlineSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLocalSuggesting, setIsLocalSuggesting] = useState(false);
  const [isOnlineSuggesting, setIsOnlineSuggesting] = useState(false);
  const searchRequestId = useRef(0);

  const handleLaunch = async () => {
    if (!query.trim()) return;
    const sessionId = await launch(query);
    if (sessionId) {
      router.push(`/analysis/${sessionId}`);
    }
  };

  const handleChip = async (chip: string) => {
    setQuery(chip);
    const sessionId = await launch(chip);
    if (sessionId) {
      router.push(`/analysis/${sessionId}`);
    }
  };

  useEffect(() => {
    if (!showSuggestions) return;

    const handle = window.setTimeout(async () => {
      const trimmed = query.trim();
      const requestId = ++searchRequestId.current;

      setIsLocalSuggesting(true);
      setIsOnlineSuggesting(Boolean(trimmed));

      void searchMutations(trimmed, "local")
        .then((nextLocal) => {
          if (requestId !== searchRequestId.current) return;
          setLocalSuggestions(nextLocal);
        })
        .finally(() => {
          if (requestId !== searchRequestId.current) return;
          setIsLocalSuggesting(false);
        });

      if (!trimmed) {
        setOnlineSuggestions([]);
        setIsOnlineSuggesting(false);
        return;
      }

      void searchMutations(trimmed, "online")
        .then((nextOnline) => {
          if (requestId !== searchRequestId.current) return;
          setOnlineSuggestions(nextOnline);
        })
        .finally(() => {
          if (requestId !== searchRequestId.current) return;
          setIsOnlineSuggesting(false);
        });
    }, 200);

    return () => window.clearTimeout(handle);
  }, [query, showSuggestions]);

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{ background: "var(--background)", color: "var(--foreground)" }}
    >
      <main className="flex-1">
        <section
          className="flex-1 flex flex-col items-center justify-center border-b"
          style={{ borderColor: "var(--border)", background: "var(--background)" }}
        >
          <div className="max-w-4xl w-full mx-auto px-6 md:px-16 py-20 md:py-32">
            <div className="text-center mb-12">
              <p className="text-sm font-mono tracking-widest uppercase text-primary mb-3">
                Discovery Workspace
              </p>
              <h1 className="text-4xl md:text-5xl font-bold leading-tight mb-5 tracking-tight">
                New Drug Discovery Run
              </h1>
              <p className="text-base text-muted-foreground max-w-2xl mx-auto">
                Enter a gene mutation to initiate the 22-agent drug discovery pipeline.
                Our autonomous system will parse the structure, generate novel candidates, and validate through MD.
              </p>
            </div>

            <div className="max-w-3xl mx-auto w-full mb-10" data-tour="query-panel">
              <div className="flex gap-3 mb-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="Search mutation (e.g. EGFR T790M)..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleLaunch()}
                    onFocus={() => setShowSuggestions(true)}
                    onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                    className="w-full pl-10 pr-4 py-4 rounded-xl border text-base outline-none transition-all bg-input focus:ring-2 focus:ring-primary/20"
                    style={{
                      borderColor: "var(--border)",
                      color: "var(--foreground)",
                    }}
                  />
                  {showSuggestions &&
                    (isLocalSuggesting ||
                      isOnlineSuggesting ||
                      localSuggestions.length > 0 ||
                      onlineSuggestions.length > 0) && (
                    <div
                      className="absolute z-20 mt-2 w-full rounded-xl border shadow-xl overflow-hidden"
                      style={{ borderColor: "var(--border)", background: "var(--card)" }}
                      role="listbox"
                    >
                      <div className="grid md:grid-cols-2">
                        <div className="border-r" style={{ borderColor: "var(--border)" }}>
                          <div className="px-4 py-2 text-[11px] font-semibold tracking-wide uppercase text-muted-foreground bg-muted/30">
                            Local Library
                          </div>
                          {isLocalSuggesting && localSuggestions.length === 0 && (
                            <div className="px-4 py-2 text-xs text-muted-foreground animate-pulse">
                              Scanning local dataset...
                            </div>
                          )}
                          {!isLocalSuggesting && localSuggestions.length === 0 && query.trim() && (
                            <div className="px-4 py-2 text-xs text-muted-foreground">
                              No local matches
                            </div>
                          )}
                          {localSuggestions.map((item, index) => (
                            <button
                              key={`local-${item}-${index}`}
                              type="button"
                              className="w-full text-left px-4 py-3 text-sm hover:bg-muted transition-colors flex items-center justify-between group"
                              onMouseDown={(event) => event.preventDefault()}
                              onClick={() => {
                                setQuery(item);
                                setShowSuggestions(false);
                              }}
                            >
                              <span>{item}</span>
                              <span className="text-[10px] uppercase font-bold text-emerald-500 opacity-0 group-hover:opacity-100 transition-opacity">Dataset</span>
                            </button>
                          ))}
                        </div>
                        <div>
                          <div className="px-4 py-2 text-[11px] font-semibold tracking-wide uppercase text-muted-foreground bg-muted/30">
                            Remote Scientific API
                          </div>
                          {isOnlineSuggesting && onlineSuggestions.length === 0 && (
                            <div className="px-4 py-2 text-xs text-muted-foreground animate-pulse">Fetching...</div>
                          )}
                          {!isOnlineSuggesting && onlineSuggestions.length === 0 && query.trim() && (
                            <div className="px-4 py-2 text-xs text-muted-foreground">
                              No online matches
                            </div>
                          )}
                          {onlineSuggestions.map((item, index) => (
                            <button
                              key={`online-${item}-${index}`}
                              type="button"
                              className="w-full text-left px-4 py-3 text-sm hover:bg-muted transition-colors flex items-center justify-between group"
                              onMouseDown={(event) => event.preventDefault()}
                              onClick={() => {
                                setQuery(item);
                                setShowSuggestions(false);
                              }}
                            >
                              <span>{item}</span>
                              <span className="text-[10px] uppercase font-bold text-blue-500 opacity-0 group-hover:opacity-100 transition-opacity">Remote</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                <button
                  type="button"
                  onClick={handleLaunch}
                  disabled={isLoading || !query.trim()}
                  className="inline-flex items-center gap-2 px-8 py-3 rounded-xl text-sm font-bold shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:scale-100"
                  style={{
                    background: "var(--primary)",
                    color: "var(--primary-foreground)",
                  }}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Launching...
                    </>
                  ) : (
                    <>
                      Start Pipeline
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <span className="text-xs font-medium text-muted-foreground">Try a demo:</span>
                {DEMO_CHIPS.map((chip) => (
                  <button
                    type="button"
                    key={chip}
                    onClick={() => handleChip(chip)}
                    disabled={isLoading}
                    className="px-3 py-1.5 rounded-full text-xs font-medium border border-border bg-card hover:bg-muted hover:border-primary/30 transition-all disabled:opacity-50"
                  >
                    {chip}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex flex-col items-center gap-4">
              <button
                type="button"
                onClick={() => handleChip("EGFR T790M")}
                disabled={isLoading}
                className="group relative inline-flex items-center gap-3 px-8 py-4 rounded-xl text-sm font-bold bg-zinc-900 text-white hover:bg-black transition-all overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <Dna className="w-5 h-5 text-primary group-hover:rotate-12 transition-transform" />
                <span>Run Interactive EGFR Tutorial</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
              
              <Link
                href="/"
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                style={{ borderColor: "var(--border)" }}
              >
                ← Return to Platform Overview
              </Link>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
