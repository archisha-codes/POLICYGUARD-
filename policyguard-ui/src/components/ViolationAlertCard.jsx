export default function ViolationAlertCard({ evidence, justification }) {
  return (
    <div className="bg-red-50 border-l-4 border-red-600 p-4 rounded-lg">
      <p className="text-red-700 font-semibold mb-2">
        Triggered RBI Evidence
      </p>

      <blockquote className="italic text-gray-700 border-l-2 pl-3">
        “{evidence}”
      </blockquote>

      <p className="mt-3 text-sm text-gray-600">
        <strong>AI Justification:</strong> {justification}
      </p>
    </div>
  );
}
