import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
} from "recharts";

const ALTO = 320;

const COLORES = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#8b5cf6",
  "#ef4444",
  "#06b6d4",
  "#f97316",
  "#ec4899",
];

const TICK_STYLE = { fontSize: 12, fill: "#6b7280" };

function formatearNumero(valor) {
  if (typeof valor !== "number") return valor;
  return new Intl.NumberFormat("es-AR", { maximumFractionDigits: 2 }).format(
    valor,
  );
}

function VistaBar({ data, config }) {
  const { x_key, y_key } = config;
  const rotar = data.length > 5;

  return (
    <ResponsiveContainer width="100%" height={ALTO}>
      <BarChart
        data={data}
        margin={{ top: 8, right: 16, left: 0, bottom: rotar ? 64 : 8 }}
      >
        <XAxis
          dataKey={x_key}
          tick={TICK_STYLE}
          angle={rotar ? -45 : 0}
          textAnchor={rotar ? "end" : "middle"}
          interval={0}
        />
        <YAxis tick={TICK_STYLE} />
        <Tooltip />
        <Bar dataKey={y_key} fill={COLORES[0]} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function VistaLine({ data, config }) {
  const { x_key, y_key } = config;

  return (
    <ResponsiveContainer width="100%" height={ALTO}>
      <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey={x_key} tick={TICK_STYLE} />
        <YAxis tick={TICK_STYLE} />
        <Tooltip />
        <Line
          type="monotone"
          dataKey={y_key}
          stroke={COLORES[0]}
          strokeWidth={2}
          dot={{ r: 3, fill: COLORES[0] }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

function VistaPie({ data, config }) {
  const { name_key, value_key } = config;

  return (
    <ResponsiveContainer width="100%" height={ALTO}>
      <PieChart>
        <Pie
          data={data}
          dataKey={value_key}
          nameKey={name_key}
          cx="50%"
          cy="45%"
          outerRadius={110}
          label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
          labelLine={true}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORES[i % COLORES.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}

function VistaKpi({ data, config }) {
  const { value_key, label } = config;
  const valor = data[0]?.[value_key];

  return (
    <div
      className="flex flex-col items-center justify-center"
      style={{ height: ALTO }}
    >
      <p className="text-5xl font-bold text-gray-900 tabular-nums">
        {formatearNumero(valor)}
      </p>
      <p className="text-sm text-gray-500 mt-3">{label}</p>
    </div>
  );
}

function VistaMultibar({ data, config }) {
  const { x_key, y_keys } = config;
  const rotar = data.length > 5;

  return (
    <ResponsiveContainer width="100%" height={ALTO}>
      <BarChart
        data={data}
        margin={{ top: 8, right: 16, left: 0, bottom: rotar ? 64 : 8 }}
      >
        <XAxis
          dataKey={x_key}
          tick={TICK_STYLE}
          angle={rotar ? -45 : 0}
          textAnchor={rotar ? "end" : "middle"}
          interval={0}
        />
        <YAxis tick={TICK_STYLE} />
        <Tooltip />
        <Legend />
        {y_keys.map((key, i) => (
          <Bar
            key={key}
            dataKey={key}
            fill={COLORES[i % COLORES.length]}
            radius={[4, 4, 0, 0]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

const VISTAS = {
  bar: VistaBar,
  line: VistaLine,
  pie: VistaPie,
  kpi: VistaKpi,
  multibar: VistaMultibar,
};

export default function ChartRenderer({ chart_type, chart_config, data }) {
  if (!chart_type || chart_type === "table" || !chart_config || !data?.length) {
    return null;
  }

  const Vista = VISTAS[chart_type];
  if (!Vista) return null;

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <Vista data={data} config={chart_config} />
    </div>
  );
}
