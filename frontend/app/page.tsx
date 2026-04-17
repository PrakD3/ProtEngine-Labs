"use client";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  ArrowRight,
  BarChart3,
  ChevronRight,
  Dna,
  FlaskConical,
  Hospital,
  Moon,
  Search,
  Shield,
  Sun,
  TreePine,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { useAnalysis } from "@/app/hooks/useAnalysis";
import { useTheme } from "@/app/hooks/useTheme";

gsap.registerPlugin(ScrollTrigger);

const DEMO_CHIPS = ["EGFR T790M", "HIV K103N", "BRCA1 5382insC", "TP53 R248W"];

const FEATURES = [
  {
    icon: Dna,
    title: "De Novo Generation",
    desc: "Generates novel molecules beyond existing databases via RDKit scaffold hopping.",
  },
  {
    icon: Shield,
    title: "Selectivity Dual-Docking",
    desc: "Scores safety vs. healthy proteins in parallel. Selectivity ratio = target / off-target.",
  },
  {
    icon: FlaskConical,
    title: "ADMET Screening",
    desc: "50+ drug-likeness endpoints: Lipinski, PAINS filter, BBB, bioavailability, toxicophore images.",
  },
  {
    icon: TreePine,
    title: "Evolution Tree",
    desc: "Visualizes how seed molecules transform into leads via scaffold hop + bioisostere operations.",
  },
  {
    icon: Hospital,
    title: "Clinical Trial Matching",
    desc: "Links your discovery to active ClinicalTrials.gov trials in real time.",
  },
  {
    icon: BarChart3,
    title: "LangSmith Tracing",
    desc: "Enterprise observability on every agent call — latency, tokens, decisions, fully auditable.",
  },
];

const STEPS = [
  {
    num: "01",
    title: "Enter Query",
    desc: "Type a mutation like 'EGFR T790M' or a disease target.",
  },
  {
    num: "02",
    title: "18-Agent Pipeline",
    desc: "Fetch → Structure → Generate → Dock → Select → ADMET → Optimize → Report.",
  },
  {
    num: "03",
    title: "Ranked Report",
    desc: "Top leads with docking scores, selectivity ratios, clinical trials, and full evidence.",
  },
];

export default function HomePage() {
  const router = useRouter();
  const { isDark, toggleDark } = useTheme();
  const { launch, isLoading } = useAnalysis();
  const [query, setQuery] = useState("");
  const heroRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    gsap.from(".hero-word", {
      opacity: 0,
      y: 50,
      duration: 0.6,
      stagger: 0.06,
      ease: "power3.out",
      delay: 0.3,
    });
    gsap.from(".hero-sub", {
      opacity: 0,
      y: 20,
      duration: 0.5,
      delay: 0.8,
    });
    gsap.from(".hero-cta", {
      opacity: 0,
      y: 20,
      duration: 0.4,
      stagger: 0.1,
      delay: 1.1,
    });
    gsap.from(".stat-card", {
      scrollTrigger: { trigger: ".stats-bar", start: "top 80%" },
      opacity: 0,
      y: 25,
      duration: 0.5,
      stagger: 0.1,
    });
    gsap.from(".feature-card", {
      scrollTrigger: { trigger: ".features-grid", start: "top 75%" },
      opacity: 0,
      y: 40,
      duration: 0.5,
      stagger: 0.07,
      ease: "back.out(1.1)",
    });
    gsap.from(".step-card", {
      scrollTrigger: { trigger: ".steps-row", start: "top 80%" },
      opacity: 0,
      x: -30,
      duration: 0.5,
      stagger: 0.15,
    });
  }, []);

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

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--background)" }}>
      {/* Sticky Header */}
      <header
        className="sticky top-0 z-50 border-b px-6 py-4 flex items-center justify-between backdrop-blur-sm"
        style={{
          background: "var(--header-bg)",
          borderColor: "var(--header-border)",
        }}
      >
        <div className="flex items-center gap-2 font-bold text-lg">
          <Dna className="w-6 h-6" style={{ color: "var(--primary)" }} />
          <span style={{ color: "var(--foreground)" }}>Drug Discovery AI</span>
        </div>
        <nav
          className="hidden md:flex items-center gap-6 text-sm"
          style={{ color: "var(--muted-foreground)" }}
        >
          <a href="#features" className="hover:opacity-80 transition-opacity">
            Features
          </a>
          <a href="#pipeline" className="hover:opacity-80 transition-opacity">
            Pipeline
          </a>
          <Link href="/discoveries" className="hover:opacity-80 transition-opacity">
            Discoveries
          </Link>
          <Link href="/settings" className="hover:opacity-80 transition-opacity">
            Settings
          </Link>
        </nav>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={toggleDark}
            className="p-2 rounded-lg border transition-colors"
            style={{
              borderColor: "var(--border)",
              color: "var(--muted-foreground)",
            }}
            aria-label="Toggle theme"
          >
            {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
          <button
            type="button"
            onClick={handleLaunch}
            disabled={isLoading}
            className="px-4 py-2 rounded-lg font-medium text-sm transition-opacity hover:opacity-90"
            style={{
              background: "var(--primary)",
              color: "var(--primary-foreground)",
            }}
          >
            {isLoading ? "Starting..." : "Launch Analysis"}
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section
        ref={heroRef}
        className="relative flex-1 min-h-[90vh] flex items-center px-6 md:px-16 py-20 overflow-hidden"
      >
        {/* Background dot grid */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage: "radial-gradient(circle, var(--border) 1px, transparent 1px)",
            backgroundSize: "32px 32px",
            opacity: 0.5,
          }}
        />
        {/* Amber gradient mesh */}
        <div
          className="absolute top-0 right-0 w-96 h-96 rounded-full pointer-events-none"
          style={{
            background: "radial-gradient(circle, rgba(251,191,36,0.15) 0%, transparent 70%)",
            filter: "blur(40px)",
          }}
        />

        <div className="relative z-10 max-w-6xl mx-auto w-full grid md:grid-cols-2 gap-12 items-center">
          {/* Left */}
          <div>
            <div
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border mb-6"
              style={{
                borderColor: "var(--primary)",
                color: "var(--accent-foreground)",
                background: "var(--accent)",
              }}
            >
              <Zap className="w-3 h-3" />
              18 AI Agents · v3.0
            </div>
            <h1 className="text-5xl md:text-6xl font-bold leading-tight mb-6">
              {["Drug", "Discovery", "Reimagined"].map((word) => (
                <span
                  key={word}
                  className="hero-word inline-block mr-3"
                  style={{ color: "var(--foreground)" }}
                >
                  {word}
                </span>
              ))}
            </h1>
            <p
              className="hero-sub text-lg mb-8 leading-relaxed"
              style={{ color: "var(--muted-foreground)" }}
            >
              Generate novel molecules, predict selectivity against healthy proteins, match active
              clinical trials — all in under 60 seconds.
            </p>

            {/* Search Bar */}
            <div className="hero-cta flex gap-3 mb-4">
              <div className="relative flex-1">
                <Search
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4"
                  style={{ color: "var(--muted-foreground)" }}
                />
                <input
                  type="text"
                  placeholder="e.g. EGFR T790M"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleLaunch()}
                  className="w-full pl-10 pr-4 py-3 rounded-xl border text-sm outline-none transition-colors"
                  style={{
                    background: "var(--input)",
                    borderColor: "var(--border)",
                    color: "var(--foreground)",
                  }}
                />
              </div>
              <button
                type="button"
                onClick={handleLaunch}
                disabled={isLoading || !query.trim()}
                className="flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm transition-all hover:opacity-90 disabled:opacity-50"
                style={{
                  background: "var(--primary)",
                  color: "var(--primary-foreground)",
                }}
              >
                {isLoading ? (
                  "..."
                ) : (
                  <>
                    <span>Launch</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>

            {/* Demo Chips */}
            <div className="hero-cta flex flex-wrap gap-2">
              {DEMO_CHIPS.map((chip) => (
                <button
                  type="button"
                  key={chip}
                  onClick={() => handleChip(chip)}
                  disabled={isLoading}
                  className="px-3 py-1 rounded-lg text-xs font-mono border transition-all hover:opacity-80 disabled:opacity-50"
                  style={{
                    background: "var(--accent)",
                    borderColor: "var(--border)",
                    color: "var(--accent-foreground)",
                  }}
                >
                  {chip}
                </button>
              ))}
            </div>
            <p className="mt-4 text-xs" style={{ color: "var(--muted-foreground)" }}>
              ⚠ Computational predictions only. Not clinical advice.
            </p>
          </div>

          {/* Right — Animated Pipeline SVG */}
          <div className="hidden md:flex items-center justify-center">
            <PipelineAnimation />
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section
        className="stats-bar border-y py-8"
        style={{ borderColor: "var(--border)", background: "var(--muted)" }}
      >
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6 px-6">
          {[
            { value: "18", label: "AI Agents" },
            { value: "4", label: "Scientific Databases" },
            { value: "Neon", label: "Discovery DB" },
            { value: "Live", label: "Selectivity Analysis" },
          ].map((s) => (
            <div key={s.label} className="stat-card text-center">
              <div className="text-3xl font-bold" style={{ color: "var(--primary)" }}>
                {s.value}
              </div>
              <div className="text-sm mt-1" style={{ color: "var(--muted-foreground)" }}>
                {s.label}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-20 px-6 md:px-16">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-3" style={{ color: "var(--foreground)" }}>
              Six Differentiators
            </h2>
            <p className="text-sm" style={{ color: "var(--muted-foreground)" }}>
              What judges won&apos;t see elsewhere
            </p>
          </div>
          <div className="features-grid grid md:grid-cols-3 gap-6">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div
                key={title}
                className="feature-card p-6 rounded-xl border transition-all hover:shadow-md"
                style={{
                  background: "var(--card)",
                  borderColor: "var(--border)",
                }}
              >
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center mb-4"
                  style={{ background: "var(--accent)" }}
                >
                  <Icon className="w-5 h-5" style={{ color: "var(--primary)" }} />
                </div>
                <h3 className="font-semibold mb-2" style={{ color: "var(--foreground)" }}>
                  {title}
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: "var(--muted-foreground)" }}>
                  {desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="pipeline" className="py-20 px-6 md:px-16" style={{ background: "var(--muted)" }}>
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-3" style={{ color: "var(--foreground)" }}>
              How It Works
            </h2>
          </div>
          <div className="steps-row grid md:grid-cols-3 gap-8 items-center">
            {STEPS.map((s, i) => (
              <div key={s.num} className="step-card flex flex-col items-center text-center">
                <div
                  className="w-14 h-14 rounded-full flex items-center justify-center text-xl font-bold mb-4 border-2"
                  style={{
                    borderColor: "var(--primary)",
                    color: "var(--primary)",
                    background: "var(--background)",
                  }}
                >
                  {s.num}
                </div>
                <h3 className="font-semibold mb-2" style={{ color: "var(--foreground)" }}>
                  {s.title}
                </h3>
                <p className="text-sm" style={{ color: "var(--muted-foreground)" }}>
                  {s.desc}
                </p>
                {i < STEPS.length - 1 && (
                  <ChevronRight
                    className="hidden md:block absolute translate-x-24 w-6 h-6"
                    style={{ color: "var(--border)" }}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer
        className="border-t py-8 px-6 text-center text-sm"
        style={{
          borderColor: "var(--border)",
          color: "var(--muted-foreground)",
        }}
      >
        <div className="flex items-center justify-center gap-2 mb-2">
          <Dna className="w-4 h-4" style={{ color: "var(--primary)" }} />
          <span className="font-semibold" style={{ color: "var(--foreground)" }}>
            Drug Discovery AI
          </span>
        </div>
        <p>Built for hackathon. Computational predictions only. Not for clinical use.</p>
      </footer>
    </div>
  );
}

function PipelineAnimation() {
  const agents = [
    "Mutation Parser",
    "Fetch (4x)",
    "Structure Prep",
    "Pocket Detection",
    "Molecule Gen",
    "Docking",
    "Selectivity",
    "ADMET",
    "Report",
  ];

  return (
    <div className="relative w-72">
      <div className="flex flex-col gap-2">
        {agents.map((agent, i) => (
          <div
            key={agent}
            className="flex items-center gap-3 px-4 py-2 rounded-lg border"
            style={{
              background: "var(--card)",
              borderColor: i === 5 ? "var(--primary)" : "var(--border)",
              borderWidth: i === 5 ? 2 : 1,
              animation: `fadeInSlide 0.4s ease ${i * 0.15}s both`,
            }}
          >
            <div
              className="w-2 h-2 rounded-full shrink-0"
              style={{
                background:
                  i < 5 ? "var(--selectivity-high)" : i === 5 ? "var(--primary)" : "var(--border)",
              }}
            />
            <span className="text-xs font-medium" style={{ color: "var(--foreground)" }}>
              {agent}
            </span>
          </div>
        ))}
      </div>
      <style>{`
        @keyframes fadeInSlide {
          from { opacity: 0; transform: translateX(20px); }
          to { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </div>
  );
}
