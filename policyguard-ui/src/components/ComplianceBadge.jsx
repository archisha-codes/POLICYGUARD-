export default function ComplianceBadge({ status }) {
  const styles = {
    COMPLIANT: "bg-green-100 text-green-700",
    PARTIALLY_COMPLIANT: "bg-yellow-100 text-yellow-700",
    NON_COMPLIANT: "bg-red-100 text-red-700",
  };

  const labels = {
    COMPLIANT: "Compliant",
    PARTIALLY_COMPLIANT: "Partially Compliant",
    NON_COMPLIANT: "Non-Compliant",
  };

  // Safety fallback (very important)
  const safeStatus = styles[status] ? status : "NON_COMPLIANT";

  return (
    <span
      className={`px-4 py-1 rounded-full font-semibold ${styles[safeStatus]}`}
    >
      {labels[safeStatus]}
    </span>
  );
}
