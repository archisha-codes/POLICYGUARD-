export default function PolicyCoverageBar({ coverage }) {
  return (
    <div>
      <p className="text-sm text-gray-600 mb-1">
        Policy Coverage: {coverage}%
      </p>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className="bg-green-600 h-3 rounded-full transition-all"
          style={{ width: `${coverage}%` }}
        />
      </div>
    </div>
  );
}
