import React from 'react';

interface DomainPoint {
  code: string;
  name: string;
  score: number | null;
}

interface DomainRadarProps {
  domains: DomainPoint[];
  /** Target score (renders a dashed ring). Default 3.0. */
  target?: number;
  /** Overall score for the center label. */
  overall?: number | null;
  /** SVG box size in px. */
  size?: number;
}

const colorForScore = (s: number | null): string => {
  if (s == null) return 'var(--muted-2)';
  if (s < 1.5) return 'var(--danger)';
  if (s < 2.5) return 'var(--warn)';
  if (s < 3.5) return 'var(--accent)';
  return 'var(--ok)';
};

/**
 * Radar / spider chart for the 5-domain RMI snapshot.
 * Score scale 0-5. Renders concentric polygon rings, a dashed target ring,
 * the actual score polygon, axis lines, and labels at each vertex.
 */
export const DomainRadar: React.FC<DomainRadarProps> = ({
  domains,
  target = 3.0,
  overall,
  size = 360,
}) => {
  const cx = size / 2;
  const cy = size / 2;
  const radius = size / 2 - 56; // leave room for labels
  const maxScore = 5;
  const n = domains.length;

  // Each axis angle, starting at top (-π/2) and going clockwise.
  const angleFor = (i: number) => -Math.PI / 2 + (i * 2 * Math.PI) / n;

  // Point at (score) along axis i; clamped 0-5.
  const pointFor = (i: number, score: number) => {
    const r = (Math.min(Math.max(score, 0), maxScore) / maxScore) * radius;
    const a = angleFor(i);
    return [cx + Math.cos(a) * r, cy + Math.sin(a) * r] as [number, number];
  };

  // Polygon path string for any uniform-radius ring at score s.
  const ringPath = (s: number) =>
    domains.map((_, i) => {
      const [x, y] = pointFor(i, s);
      return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
    }).join(' ') + ' Z';

  // Polygon path for the actual scores (skip null = treat as 0).
  const scorePath = domains
    .map((d, i) => {
      const [x, y] = pointFor(i, d.score ?? 0);
      return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(' ') + ' Z';

  // Pick a representative tone for the score polygon based on overall.
  const tone = colorForScore(overall ?? null);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        role="img"
        aria-label="Domain radar"
        style={{ display: 'block', maxWidth: '100%' }}
      >
        {/* Concentric scale rings 1..5 */}
        {[1, 2, 3, 4, 5].map((s) => (
          <path
            key={s}
            d={ringPath(s)}
            fill="none"
            stroke="var(--line)"
            strokeWidth={1}
          />
        ))}

        {/* Filled background of innermost (just visual depth) */}
        <path d={ringPath(5)} fill="var(--surface-2)" opacity={0.5} />

        {/* Re-draw rings on top of the fill so they're visible */}
        {[1, 2, 3, 4, 5].map((s) => (
          <path
            key={`o-${s}`}
            d={ringPath(s)}
            fill="none"
            stroke="var(--line)"
            strokeWidth={1}
          />
        ))}

        {/* Axes */}
        {domains.map((_, i) => {
          const [x, y] = pointFor(i, maxScore);
          return (
            <line
              key={`axis-${i}`}
              x1={cx}
              y1={cy}
              x2={x}
              y2={y}
              stroke="var(--line)"
              strokeWidth={1}
            />
          );
        })}

        {/* Dashed target ring */}
        <path
          d={ringPath(target)}
          fill="none"
          stroke="var(--ink-2)"
          strokeWidth={1.25}
          strokeDasharray="4 4"
          opacity={0.55}
        />

        {/* Score polygon */}
        <path
          d={scorePath}
          fill={tone}
          fillOpacity={0.18}
          stroke={tone}
          strokeWidth={2}
          strokeLinejoin="round"
        />

        {/* Score points */}
        {domains.map((d, i) => {
          const [x, y] = pointFor(i, d.score ?? 0);
          return (
            <circle
              key={`pt-${i}`}
              cx={x}
              cy={y}
              r={4}
              fill="var(--surface)"
              stroke={colorForScore(d.score)}
              strokeWidth={2}
            />
          );
        })}

        {/* Axis labels at the outer edge */}
        {domains.map((d, i) => {
          const a = angleFor(i);
          const labelR = radius + 22;
          const x = cx + Math.cos(a) * labelR;
          const y = cy + Math.sin(a) * labelR;
          // Align text based on quadrant
          const cos = Math.cos(a);
          const sin = Math.sin(a);
          let textAnchor: 'start' | 'middle' | 'end' = 'middle';
          if (cos > 0.25) textAnchor = 'start';
          else if (cos < -0.25) textAnchor = 'end';
          const dy = sin > 0.5 ? 12 : sin < -0.5 ? 0 : 4;
          const scoreStr = d.score != null ? d.score.toFixed(2) : '—';
          return (
            <g key={`lbl-${i}`}>
              <text
                x={x}
                y={y}
                textAnchor={textAnchor}
                dy={dy}
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 11,
                  fontWeight: 600,
                  fill: 'var(--ink)',
                  letterSpacing: '0.04em',
                }}
              >
                {d.code}
              </text>
              <text
                x={x}
                y={y}
                textAnchor={textAnchor}
                dy={dy + 14}
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 11,
                  fill: colorForScore(d.score),
                  fontWeight: 600,
                }}
              >
                {scoreStr}
              </text>
            </g>
          );
        })}

        {/* Center label: overall RMI */}
        {overall != null && (
          <g>
            <text
              x={cx}
              y={cy - 4}
              textAnchor="middle"
              style={{
                fontFamily: "'Instrument Serif', serif",
                fontSize: 26,
                fill: 'var(--ink)',
              }}
            >
              {overall.toFixed(2)}
            </text>
            <text
              x={cx}
              y={cy + 14}
              textAnchor="middle"
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 9.5,
                fill: 'var(--muted)',
                letterSpacing: '0.08em',
              }}
            >
              RMI
            </text>
          </g>
        )}
      </svg>

      {/* Legend */}
      <div
        style={{
          display: 'flex',
          gap: 18,
          marginTop: 14,
          fontSize: 11.5,
          color: 'var(--muted)',
          flexWrap: 'wrap',
          justifyContent: 'center',
        }}
      >
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
          <span
            style={{
              width: 14,
              height: 2,
              background: 'var(--ink-2)',
              opacity: 0.55,
              borderRadius: 1,
            }}
          />
          Target {target.toFixed(1)}
        </span>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
          <span
            style={{
              width: 12,
              height: 12,
              borderRadius: 2,
              background: tone,
              opacity: 0.3,
              border: `1.5px solid ${tone}`,
            }}
          />
          Current scores
        </span>
        <span style={{ color: 'var(--muted-2)' }}>Scale: 1 – 5</span>
      </div>
    </div>
  );
};

export default DomainRadar;
