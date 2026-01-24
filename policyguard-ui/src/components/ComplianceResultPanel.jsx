import ComplianceStatusBadge from \"./ComplianceBadge\";
import RiskMeter from \"./RiskMeter\";
import ConfidenceBar from \"./ConfidenceBar\";
import PolicyCoverageBar from \"./PolicyCoverageBar\";
import ViolationalAlertCard from \"./ViolationalAlertCard\";
import RiskDecomposition from \"./RiskDecomposition\";

export default function ComplianceResultPanel({ result }) {
  return (
    <div className=\"space-y-6\">
      <ComplianceStatusBadge status={result.compliance_status} />
      
      <div className=\"grid grid-cols-1 md:grid-cols-2 gap-6\">
        <RiskMeter risk={result.risk_score} />
        <div className=\"space-y-4\">
          <div className=\"bg-white p-4 rounded-xl shadow space-y-4\">
            <ConfidenceBar confidence={result.confidence_score} />
            <PolicyCoverageBar coverage={result.policy_coverage_percentage} />
          </div>
          <RiskDecomposition decomposition={result.risk_decomposition} />
        </div>
      </div>

      <ViolationalAlertCard 
        evidence={result.evidence}
        justification={result.justification}
      />
    </div>
  );
}
