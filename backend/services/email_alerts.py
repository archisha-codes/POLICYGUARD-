# backend/services/email_alerts.py
import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailAlertSystem:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("ALERT_EMAIL")
        self.sender_password = os.getenv("ALERT_EMAIL_PASSWORD")
        
        if not self.sender_email:
            logger.warning("⚠️ Email Alert System not configured (Missing Env Vars)")

    def _send_email(self, recipient: str, subject: str, body: str):
        """Internal method to send email with error handling"""
        if not self.sender_email or not self.sender_password:
            logger.info(f"📧 [Mock Email] To: {recipient} | Subject: {subject}")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            logger.info(f"✅ Email sent to {recipient}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False

    def send_transaction_violation_alert(self, transaction_data: Dict, violation_type: str, recipient: str):
        """Standard Violation Alert"""
        subject = f"🚨 ALERT: Transaction Violation - {violation_type}"
        body = f"""
        <h2>Transaction Violation Detected</h2>
        <p><strong>Type:</strong> {violation_type}</p>
        <p><strong>ID:</strong> {transaction_data.get('transaction_id')}</p>
        <p><strong>Risk Score:</strong> {transaction_data.get('risk_score', 'N/A')}</p>
        <p><strong>Reason:</strong> {transaction_data.get('reason')}</p>
        <hr>
        <p><i>PolicyGuard Automated Auditor</i></p>
        """
        self._send_email(recipient, subject, body)

    def send_kyc_incomplete_alert(self, transaction_data: Dict, missing_docs: str, recipient: str):
        """KYC Alert"""
        subject = f"⚠️ ACTION REQUIRED: KYC Incomplete - {transaction_data.get('customer_id')}"
        body = f"""
        <h2>KYC Incomplete</h2>
        <p><strong>Customer:</strong> {transaction_data.get('customer_id')}</p>
        <p><strong>Missing Documentation:</strong> {missing_docs}</p>
        <p>Please upload the required documents to the secure portal.</p>
        """
        self._send_email(recipient, subject, body)

    def send_loan_risk_alert(self, transaction_data: Dict, risk_breakdown: Dict, recipient: str):
        """
        Loan Approval Risk Alert.
        Highlights AML exposure and Sanctions specifically for Credit Teams.
        """
        subject = f"⛔ LOAN RISK ALERT: Application {transaction_data.get('transaction_id')}"
        body = f"""
        <h2 style="color: #D32F2F;">Loan Application Flagged</h2>
        <p><strong>Applicant ID:</strong> {transaction_data.get('customer_id')}</p>
        <p><strong>Requested Amount:</strong> {transaction_data.get('currency')} {transaction_data.get('amount')}</p>
        
        <h3>Risk Decomposition:</h3>
        <ul>
            <li><strong>AML Risk:</strong> {risk_breakdown.get('aml_risk', 0)}%</li>
            <li><strong>Sanctions Exposure:</strong> {risk_breakdown.get('sanctions_risk', 0)}%</li>
            <li><strong>KYC Status:</strong> {risk_breakdown.get('kyc_risk', 0)}% (Risk)</li>
        </ul>
        
        <p><strong>AI Assessment:</strong> {transaction_data.get('ai_explanation')}</p>
        <p><strong>Recommendation:</strong> Enhanced Due Diligence (EDD) Required before disbursement.</p>
        <hr>
        <p><i>PolicyGuard Credit Risk Monitor</i></p>
        """
        self._send_email(recipient, subject, body)

    def send_policy_change_alert(self, policy_update: Dict):
        """Drift Detection Alert"""
        # In prod, this would loop through a list of Compliance Officers
        recipient = self.sender_email if self.sender_email else "admin@policyguard.com"
        subject = f"📜 Regulatory Drift Detected: {policy_update['source']}"
        body = f"""
        <h2>New Regulation Indexed</h2>
        <p><strong>Source:</strong> {policy_update['source']} ({policy_update.get('region')})</p>
        <p><strong>Title:</strong> {policy_update['title']}</p>
        <p><strong>Summary:</strong> {policy_update['summary']}</p>
        <p><strong>Impact Level:</strong> {policy_update.get('impact_level')}</p>
        <hr>
        <p><strong>Action Taken:</strong> Knowledge Base updated. No manual action required.</p>
        """
        self._send_email(recipient, subject, body)