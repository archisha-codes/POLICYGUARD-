export default function StatCard({ title, value, gradient }) {
  return (
    <div
      className={`rounded-2xl p-5 text-white shadow-lg
      bg-gradient-to-r ${gradient}
      hover:scale-[1.03] transition-transform`}
    >

      <p className="text-sm opacity-80">{title}</p>
      <p className="text-3xl font-bold mt-2">{value}</p>
    </div>
  );
}
