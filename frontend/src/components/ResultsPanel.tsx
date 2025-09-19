// path: frontend/src/components/ResultsPanel.tsx
import React from "react";
import { WtnLink, findWtnUrl } from "./WtnLink";

type Props = {
  baseUrl: string;               // from your Config section
  title: string;
  payload: unknown;              // raw API response object
};

export const ResultsPanel: React.FC<Props> = ({ baseUrl, title, payload }) => {
  const wtnUrl = findWtnUrl(payload);

  return (
    <div className="rounded-2xl border border-slate-700 p-4 mt-4">
      <div className="font-semibold mb-2">{title}</div>
      <pre className="text-sm whitespace-pre-wrap break-all">
        {JSON.stringify(payload, null, 2)}
      </pre>

      {wtnUrl && (
        <WtnLink
          baseUrl={baseUrl}
          wtnPdfUrl={wtnUrl}
          className="flex gap-2 mt-3"
        />
      )}
    </div>
  );
};
