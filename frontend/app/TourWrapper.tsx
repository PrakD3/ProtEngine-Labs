"use client";

import TourGuide from "@/components/TourGuide";
import { useModeStore, ModeToggle } from "@/components/ModeToggle";
import { ReactNode } from "react";

export function TourWrapper({ children }: { children: ReactNode }) {
  const { isEasyMode } = useModeStore();
  
  return (
    <TourGuide isEasyMode={isEasyMode}>
      <ModeToggle />
      {children}
    </TourGuide>
  );
}
