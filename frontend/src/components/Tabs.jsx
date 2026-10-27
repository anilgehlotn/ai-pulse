import React from "react";

export default function Tabs({ tabs, current, onSelect }) {
  return (
    <nav className="tabs" aria-label="Sections">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          className="tab"
          aria-current={tab.id === current ? "page" : undefined}
          onClick={() => onSelect(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}
