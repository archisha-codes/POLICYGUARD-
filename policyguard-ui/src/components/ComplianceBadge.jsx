export default function ComplianceBadge({ status }) {
  const styles = {
    COMPLIANT: "bg-green-100 text-green-700",
    PARTIALLY: "bg-yellow-100 text-yellow-700",
    NON: "bg-red-100 text-red-700",
  };

  return (
    <span
      className={`px-4 py-1 rounded-full font-medium text-sm
      shadow-sm ${styles[status]}`}
    >
      {status} COMPLIANT
    </span>
  );
}

