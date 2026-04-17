"use client";
import Link from "next/link";
import { Dna, Moon, Sun, Zap } from "lucide-react";
import { useTheme } from "@/app/hooks/useTheme";

export function Header() {
  const { isDark, toggleDark } = useTheme();
  return (
    <header className="sticky top-0 z-40 border-b border-[var(--header-border)] bg-[var(--header-bg)]/95 backdrop-blur supports-[backdrop-filter]:bg-[var(--header-bg)]/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-bold text-lg">
          <Dna className="text-[var(--primary)]" size={24} />
          <span>Drug Discovery AI</span>
        </Link>
        <nav className="hidden md:flex items-center gap-6 text-sm">
          <Link href="/#features" className="text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors">Features</Link>
          <Link href="/#pipeline" className="text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors">Pipeline</Link>
          <Link href="/discoveries" className="text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors">Discoveries</Link>
          <Link href="/settings" className="text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors">Settings</Link>
        </nav>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={toggleDark}
            className="p-2 rounded-md hover:bg-[var(--muted)] transition-colors"
            aria-label="Toggle theme"
          >
            {isDark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <Link
            href="/"
            className="flex items-center gap-1.5 px-4 py-2 rounded-md bg-[var(--primary)] text-[var(--primary-foreground)] text-sm font-medium hover:bg-[var(--primary)]/90 transition-colors"
          >
            <Zap size={14} />
            Launch Analysis
          </Link>
        </div>
      </div>
    </header>
  );
}
