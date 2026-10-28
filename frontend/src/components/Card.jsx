import React from "react";

// A rounded section with an optional heading. tone="accent" gives the soft coral version.
export default function Card({ id, title, tone, className = "", children }) {
  const titleId = title ? `${id}-title` : undefined;
  return (
    <section className={`card ${tone ? `card-${tone}` : ""} ${className}`} aria-labelledby={titleId}>
      {title && <h2 id={titleId}>{title}</h2>}
      {children}
    </section>
  );
}
