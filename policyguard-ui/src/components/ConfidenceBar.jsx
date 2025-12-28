export default function ConfidenceBar({ confidence }) {
  return (
    <div>
      <p className="text-sm text-gray-600 mb-1">
        AI Confidence: {confidence}%
      </p>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className="bg-blue-600 h-3 rounded-full transition-all"
          style={{ width: `${confidence}%` }}
        />
      </div>
    </div>
  );
}
