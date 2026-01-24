import React from 'react';

const RiskDecomposition = ({ decomposition }) => {
  const metrics = [
    { label: 'AML Risk', value: decomposition?.aml_risk || 0, color: 'bg-red-500' },
    { label: 'KYC Risk', value: decomposition?.kyc_risk || 0, color: 'bg-orange-500' },
    { label: 'Policy Ambiguity', value: decomposition?.policy_ambiguity || 0, color: 'bg-yellow-500' },
    { label: 'Historical Pattern', value: decomposition?.historical_pattern || 0, color: 'bg-blue-500' },
  ];

  return (
    <div className=\"bg-white rounded-2xl shadow-lg p-6 w-full\">
      <h3 className=\"text-lg font-semibold text-gray-800 mb-4\">Explainable Risk Decomposition</h3>
      <div className=\"space-y-4\">
        {metrics.map((metric) => (
          <div key={metric.label}>
            <div className=\"flex justify-between mb-1\">
              <span className=\"text-sm font-medium text-gray-600\">{metric.label}</span>
              <span className=\"text-sm font-semibold text-gray-800\">{(metric.value * 100).toFixed(0)}%</span>
            </div>
            <div className=\"w-full bg-gray-200 rounded-full h-2\">
              <div
                className={`h-2 rounded-full ${metric.color}`}
                style={{ width: `${metric.value * 100}%` }}
              ></div>
            </div>
          </div>
        ))}
      </div>
      <p className=\"text-xs text-gray-400 mt-4 italic\">
        * Scores are decomposed using the Llama-based Governance Engine.
      </p>
    </div>
  );
};

export default RiskDecomposition;
