"""Email Alerts System for POLICYGUARD
Sends alerts for:
- Transaction violations
- KYC incomplete
- Loan risk alerts
- Policy change notifications
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
from datetime import datetime


class EmailAlertSystem:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("ALERT_EMAIL")
        self.sender_password = os.getenv("ALERT_EMAIL_PASSWORD")
        self.admin_emails = os.getenv("ADMIN_EMAILS", "").split(",")

    def send_transaction_violation_alert(self, transaction_data: Dict, violation_type: str, recipient: str):
        """Send alert for transaction policy violations"""
        subject = f"🚨 Transaction Violation Alert - {violation_type}"
        
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #d32f2f;">Transaction Violation Detected</h2>
                <p><strong>Violation Type:</strong> {violation_type}</p>
                <p><strong>Transaction ID:</strong> {transaction_data.get('transaction_id', 'N/A')}</p>
                <p><strong>Amount:</strong> ${transaction_data.get('amount', 0):,.2f}</p>
                <p><strong>User ID:</strong> {transaction_data.get('user_id', 'N/A')}</p>
                <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p><strong>Reason:</strong> {transaction_data.get('reason', 'Policy violation detected')}</p>
                <p style="color: #666; font-size: 12px;">This is an automated alert from POLICYGUARD Security System.</p>
            </body>
        </html>
        """
        
        self._send_email(recipient, subject, body)

    def send_kyc_incomplete_alert(self, user_data: Dict, recipient: str):
        """Send alert for incomplete KYC"""
        subject = "⚠️ KYC Verification Incomplete"
        
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #f57c00;">KYC Verification Required</h2>
                <p>Dear User,</p>
                <p>Your KYC verification is incomplete. Please complete the following steps:</p>
                <ul>
                    <li>Upload valid ID proof</li>
                    <li>Verify address details</li>
                    <li>Complete biometric verification</li>
                </ul>
                <p><strong>User ID:</strong> {user_data.get('user_id', 'N/A')}</p>
                <p><strong>Pending Since:</strong> {user_data.get('pending_since', 'N/A')}</p>
                <p><strong>Action Required By:</strong> {user_data.get('deadline', 'N/A')}</p>
                <hr>
                <p style="color: #666; font-size: 12px;">This is an automated alert from POLICYGUARD Compliance System.</p>
            </body>
        </html>
        """
        
        self._send_email(recipient, subject, body)

    def send_loan_risk_alert(self, loan_data: Dict, risk_score: float, recipient: str):
        """Send alert for high-risk loan applications"""
        risk_level = "HIGH" if risk_score > 0.7 else "MEDIUM" if risk_score > 0.4 else "LOW"
        risk_color = "#d32f2f" if risk_score > 0.7 else "#f57c00" if risk_score > 0.4 else "#388e3c"
        
        subject = f"🏦 Loan Risk Alert - {risk_level} Risk Detected"
        
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: {risk_color};">Loan Risk Assessment Alert</h2>
                <p><strong>Risk Level:</strong> <span style="color: {risk_color}; font-weight: bold;">{risk_level}</span></p>
                <p><strong>Risk Score:</strong> {risk_score:.2%}</p>
                <p><strong>Loan ID:</strong> {loan_data.get('loan_id', 'N/A')}</p>
                <p><strong>Amount Requested:</strong> ${loan_data.get('amount', 0):,.2f}</p>
                <p><strong>Applicant ID:</strong> {loan_data.get('user_id', 'N/A')}</p>
                <p><strong>Credit Score:</strong> {loan_data.get('credit_score', 'N/A')}</p>
                <hr>
                <p><strong>Risk Factors:</strong></p>
                <ul>
                    {''.join([f'<li>{factor}</li>' for factor in loan_data.get('risk_factors', [])])}
                </ul>
                <p style="color: #666; font-size: 12px;">This is an automated alert from POLICYGUARD Risk Management System.</p>
            </body>
        </html>
        """
        
        self._send_email(recipient, subject, body)

    def send_policy_change_alert(self, policy_data: Dict, recipients: List[str]):
        """Send alert for policy changes to all admins"""
        subject = "📋 Policy Update Notification"
        
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #1976d2;">Policy Change Notification</h2>
                <p><strong>Policy Name:</strong> {policy_data.get('policy_name', 'N/A')}</p>
                <p><strong>Change Type:</strong> {policy_data.get('change_type', 'N/A')}</p>
                <p><strong>Effective Date:</strong> {policy_data.get('effective_date', 'N/A')}</p>
                <p><strong>Modified By:</strong> {policy_data.get('modified_by', 'N/A')}</p>
                <hr>
                <p><strong>Summary of Changes:</strong></p>
                <p>{policy_data.get('summary', 'No summary provided')}</p>
                <p style="color: #666; font-size: 12px;">This is an automated notification from POLICYGUARD Policy Management System.</p>
            </body>
        </html>
        """
        
        for recipient in recipients:
            self._send_email(recipient, subject, body)

    def _send_email(self, recipient: str, subject: str, body: str):
        """Internal method to send email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = recipient
            msg['Subject'] = subject
            
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                
            print(f"✅ Alert sent to {recipient}: {subject}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {recipient}: {str(e)}")
            return False

    def send_batch_alerts(self, alerts: List[Dict]):
        """Send multiple alerts in batch"""
        results = []
        for alert in alerts:
            alert_type = alert.get('type')
            recipient = alert.get('recipient')
            data = alert.get('data', {})
            
            if alert_type == 'transaction_violation':
                result = self.send_transaction_violation_alert(
                    data, 
                    alert.get('violation_type', 'Unknown'), 
                    recipient
                )
            elif alert_type == 'kyc_incomplete':
                result = self.send_kyc_incomplete_alert(data, recipient)
            elif alert_type == 'loan_risk':
                result = self.send_loan_risk_alert(
                    data, 
                    alert.get('risk_score', 0), 
                    recipient
                )
            elif alert_type == 'policy_change':
                result = self.send_policy_change_alert(
                    data, 
                    alert.get('recipients', [])
                )
            
            results.append(result)
        
        return results


# Example usage
if __name__ == "__main__":
    alert_system = EmailAlertSystem()
    
    # Example: Transaction violation alert
    transaction = {
        'transaction_id': 'TXN12345',
        'amount': 150000,
        'user_id': 'USER001',
        'reason': 'Amount exceeds daily limit'
    }
    
    # alert_system.send_transaction_violation_alert(
    #     transaction, 
    #     'Daily Limit Exceeded', 
    #     'admin@example.com'
    # )
