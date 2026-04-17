import { Dna } from "lucide-react";
import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-[var(--border)] bg-[var(--muted)] py-8 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Dna size={18} className="text-[var(--primary)]" />
            Drug Discovery AI
          </div>
          <p className="text-xs text-[var(--muted-foreground)] text-center">
            Computational predictions only. Not clinical advice. For research purposes.
          </p>
          <div className="flex gap-4 text-xs text-[var(--muted-foreground)]">
            <Link href="/discoveries" className="hover:text-[var(--foreground)]">Discoveries</Link>
            <Link href="/settings" className="hover:text-[var(--foreground)]">Settings</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
