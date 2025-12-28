export default function RiskMeter({ risk }) {
  const color =
    risk > 70
      ? "from-red-500 to-red-700"
      : risk > 40
      ? "from-yellow-400 to-yellow-600"
      : "from-green-400 to-green-600";

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 flex flex-col items-center
      hover:shadow-2xl transition">
      <p className="text-gray-500 mb-4">Overall Risk Score</p>

      <div
        className={`w-32 h-32 rounded-full flex items-center justify-center
        bg-gradient-to-br ${color} text-white text-4xl font-bold shadow-inner`}
      >
        {risk}
      </div>

      <p className="mt-4 text-sm text-gray-400">0 = Safe · 100 = High Risk</p>
    </div>
  );
}
