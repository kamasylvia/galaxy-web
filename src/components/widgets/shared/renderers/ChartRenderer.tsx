import {
  Brush,
  CartesianGrid,
  ComposedChart,
  Customized,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface CandlePoint {
  label: string;
  open: number;
  high: number;
  low: number;
  close: number;
  up: boolean;
}

function decodeF8(v: unknown): number[] {
  if (Array.isArray(v)) return (v as unknown[]).map(Number);
  if (v && typeof v === "object") {
    const o = v as Record<string, unknown>;
    if (o.dtype === "f8" && typeof o.bdata === "string") {
      try {
        const bin = atob(o.bdata as string);
        const buf = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
        const dv = new DataView(buf.buffer);
        const out: number[] = [];
        for (let i = 0; i + 8 <= dv.byteLength; i += 8) out.push(dv.getFloat64(i, true));
        return out;
      } catch {
        return [];
      }
    }
  }
  return [];
}

function toCandles(rawData: unknown): CandlePoint[] | null {
  if (!rawData || typeof rawData !== "object") return null;
  const dataObj = rawData as Record<string, unknown>;
  if (!Array.isArray(dataObj.data) || dataObj.data.length === 0) return null;
  const trace = dataObj.data[0] as Record<string, unknown>;
  const xs = Array.isArray(trace.x) ? (trace.x as unknown[]) : [];
  const opens = decodeF8(trace.open);
  const highs = decodeF8(trace.high);
  const lows = decodeF8(trace.low);
  const closes = decodeF8(trace.close);
  if (xs.length === 0 || ![opens, highs, lows, closes].every((a) => a.length === xs.length)) return null;
  return xs.map((x, i) => ({
    label: String(x).slice(0, 10),
    open: opens[i],
    high: highs[i],
    low: lows[i],
    close: closes[i],
    up: closes[i] >= opens[i],
  }));
}

interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string;
  }[];
}

function transformToChartData(rawData: unknown): ChartData {
  if (!rawData) {
    return { labels: [], datasets: [] };
  }

  const dataObj = rawData as Record<string, unknown>;

  if (dataObj.labels && dataObj.datasets) {
    return rawData as ChartData;
  }

  const candles = toCandles(rawData);
  if (candles) {
    return {
      labels: candles.map((c) => c.label),
      datasets: [
        {
          label: "Close",
          data: candles.map((c) => c.close),
          backgroundColor: "rgba(54, 162, 235, 0.2)",
          borderColor: "rgba(54, 162, 235, 1)",
        },
      ],
    };
  }

  if (Array.isArray(rawData)) {
    const labels = rawData.map((item, index) =>
      String(
        (item as Record<string, unknown>).label ||
          (item as Record<string, unknown>).date ||
          index,
      ),
    );
    const values = rawData.map((item) =>
      Number(
        (item as Record<string, unknown>).value ||
          (item as Record<string, unknown>).price ||
          0,
      ),
    );
    return {
      labels,
      datasets: [
        {
          label: "Data",
          data: values,
          backgroundColor: "rgba(54, 162, 235, 0.2)",
          borderColor: "rgba(54, 162, 235, 1)",
        },
      ],
    };
  }

  return { labels: [], datasets: [] };
}

function CandleLayer(props: {
  points?: CandlePoint[];
  xAxisMap?: Record<string | number, { scale: (v: number) => number }>;
  yAxisMap?: Record<string | number, { scale: (v: number) => number }>;
}) {
  const { points, xAxisMap, yAxisMap } = props;
  const xScale = xAxisMap ? Object.values(xAxisMap)[0]?.scale : undefined;
  const yScale = yAxisMap ? Object.values(yAxisMap)[0]?.scale : undefined;
  if (!points || !xScale || !yScale || points.length === 0) return null;
  const n = points.length;
  const step = n > 1 ? Math.abs(xScale(1) - xScale(0)) : 12;
  const bodyW = Math.max(2, Math.min(18, step * 0.6));
  return (
    <g>
      {points.map((p, i) => {
        const x = xScale(i);
        const yO = yScale(p.open);
        const yC = yScale(p.close);
        const yH = yScale(p.high);
        const yL = yScale(p.low);
        const color = p.up ? "#00B140" : "#F4284D";
        const top = Math.min(yO, yC);
        const h = Math.max(1, Math.abs(yC - yO));
        return (
          <g key={i}>
            <line x1={x} y1={yH} x2={x} y2={yL} stroke={color} strokeWidth={1.5} />
            <rect x={x - bodyW / 2} y={top} width={bodyW} height={h} fill={p.up ? "none" : color} stroke={color} strokeWidth={1.5} />
          </g>
        );
      })}
    </g>
  );
}

interface ChartRendererProps {
  data: unknown;
  chartType?: string;
  timeRange?: string;
}

export function ChartRenderer({
  data,
  chartType: _chartType = "line",
  timeRange: _timeRange = "1d",
}: ChartRendererProps): JSX.Element {
  void _chartType;
  void _timeRange;
  const candles = toCandles(data);
  if (candles && candles.length > 0) {
    const lo = Math.min(...candles.map((c) => c.low));
    const hi = Math.max(...candles.map((c) => c.high));
    const pad = (hi - lo) * 0.05 || 1;
    const indexed = candles.map((c, i) => ({ ...c, i }));
    return (
      <div className="w-full h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={indexed} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} minTickGap={40} />
            <YAxis domain={[lo - pad, hi + pad]} tick={{ fontSize: 11 }} tickFormatter={(v: number) => v.toFixed(2)} />
            <Tooltip formatter={(value, name) => [Number(value).toFixed(2), String(name)]} labelFormatter={(l) => String(l)} />
            <Line type="monotone" dataKey="close" stroke="#8884d8" dot={false} strokeWidth={1.5} name="收盘" />
            <Customized component={<CandleLayer points={candles} />} />
            {candles.length > 30 && <Brush dataKey="label" height={24} travellerWidth={8} />}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    );
  }

  const chartData = transformToChartData(data);

  if (!chartData || chartData.labels.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
        No chart data available
      </div>
    );
  }

  return (
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData.labels.map((l, i) => ({ label: l, value: chartData.datasets[0]?.data[i] ?? 0 }))} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis dataKey="label" tick={{ fontSize: 11 }} minTickGap={40} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="#8884d8" dot={false} strokeWidth={1.5} name={chartData.datasets[0]?.label || "Data"} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
