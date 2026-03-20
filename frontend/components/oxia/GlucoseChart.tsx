import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ReferenceLine,
  ReferenceDot,
} from "recharts";
import type { AnalysisResponse } from "../../lib/types";
import { OxiaEyebrow, OxiaPanel } from "./OxiaShell";

export default function GlucoseChart(props: { analysis: AnalysisResponse }) {
  const a = props.analysis;
  const ga = a.glucose_architect;
  const curve = ga.glucose_curve as Array<{ time_mins: number; glucose_mg_dl: number }>;

  const peak = Number(ga.peak_glucose ?? 0);
  const peakTime = Number(ga.spike_time_mins ?? 0);

  const data = curve.map((p) => ({
    t: Number(p.time_mins),
    g: Number(p.glucose_mg_dl),
  }));

  const ymax = Math.max(200, peak + 20);

  return (
    <OxiaPanel
      accent="neutral"
      noOrb
      eyebrow={<OxiaEyebrow accent="neutral">Visualization</OxiaEyebrow>}
      title="Blood glucose curve"
      description="Time after eating (minutes) vs modeled mg/dL. Baseline guide in green; pink dot = predicted peak."
    >
      <div className="h-[220px] min-h-[200px] sm:h-[240px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="glucoseFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#38bdf8" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
            <XAxis
              dataKey="t"
              tick={{ fill: "#a1a1aa", fontSize: 11 }}
              axisLine={{ stroke: "#3f3f46" }}
              tickLine={{ stroke: "#3f3f46" }}
            />
            <YAxis
              domain={[60, ymax]}
              tick={{ fill: "#a1a1aa", fontSize: 11 }}
              axisLine={{ stroke: "#3f3f46" }}
              tickLine={{ stroke: "#3f3f46" }}
            />
            <Tooltip
              contentStyle={{ background: "#09090b", border: "1px solid #27272a", borderRadius: 12 }}
              labelStyle={{ color: "#a1a1aa" }}
              formatter={(value: unknown) => [`${String(value)} mg/dL`, "Glucose"]}
            />
            <ReferenceLine y={85} stroke="#4ade80" strokeDasharray="4 4" strokeOpacity={0.7} />
            <ReferenceDot x={peakTime} y={peak} r={6} fill="#fb7185" stroke="#fb7185" />
            <Area
              type="monotone"
              dataKey="g"
              stroke="#38bdf8"
              strokeWidth={2.5}
              fill="url(#glucoseFill)"
              isAnimationActive={false}
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </OxiaPanel>
  );
}
