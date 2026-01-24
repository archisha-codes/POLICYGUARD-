import React, { useState } from 'react';

const EmailAlertSettings = ({ userId }) => {
  const [alerts, setAlerts] = useState({
    transactionViolations: true,
    kycIncomplete: true,
    loanRisk: true,
    policyChange: true,
    hallucination: true,
    threshold: 'medium'
  });

  const handleToggle = (field) => {
    setAlerts(prev => ({ ...prev, [field]: !prev[field] }));
  };

  const handleSave = async () => {
    try {
      await fetch(`/api/alerts/settings/${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(alerts)
      });
      alert('Email alert settings saved');
    } catch (error) {
      console.error('Error saving settings:', error);
    }
  };

  return (
    <div className="email-alert-settings">
      <h2>Email Alert Preferences</h2>
      <div className="alert-options">
        <label>
          <input type="checkbox" checked={alerts.transactionViolations} onChange={() => handleToggle('transactionViolations')} />
          Transaction Violations
        </label>
        <label>
          <input type="checkbox" checked={alerts.kycIncomplete} onChange={() => handleToggle('kycIncomplete')} />
          KYC Incomplete Alerts
        </label>
        <label>
          <input type="checkbox" checked={alerts.loanRisk} onChange={() => handleToggle('loanRisk')} />
          Loan Risk Alerts
        </label>
        <label>
          <input type="checkbox" checked={alerts.policyChange} onChange={() => handleToggle('policyChange')} />
          Policy Change Notifications
        </label>
        <label>
          <input type="checkbox" checked={alerts.hallucination} onChange={() => handleToggle('hallucination')} />
          Hallucination Detection Alerts
        </label>
      </div>
      <div className="alert-threshold">
        <label>Alert Sensitivity:</label>
        <select value={alerts.threshold} onChange={(e) => setAlerts({...alerts, threshold: e.target.value})}>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </div>
      <button onClick={handleSave} className="btn-save">Save Email Alert Settings</button>
    </div>
  );
};

export default EmailAlertSettings;
