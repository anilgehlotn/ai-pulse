import React from "react";
import { Activity } from "lucide-react";

export default function BrandMark() {
  return (
    <span className="brand">
      <span className="brand-mark" aria-hidden="true"><Activity size={18} strokeWidth={2.5} /></span>
      AI Pulse
    </span>
  );
}
