"""AI Compliance Co-Pilot for POLICYGUARD
Provides structured JSON output with compliance status, explanation, and citations
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rag_pipeline import RAGPipeline


class ComplianceCoPilot:
    """AI Co-Pilot for compliance analysis with explainability"""
    
    def __init__(self, rag_pipeline: RAGPipeline):
        self.rag = rag_pipeline
        self.analysis_history = []
    
    def analyze_transaction(self, transaction_data: Dict) -> Dict:
        """Analyze transaction for compliance with structured JSON output
        
        Returns:
            {
                "compliance_status": "APPROVED" | "FLAGGED" | "REJECTED",
                "risk_score": 0.0-1.0,
                "explanation": "Human-readable explanation",
                "citations": [list of regulation references],
                "risk_decomposition": {...},
                "recommendations": [...]
            }
        """
        
        # Extract transaction details
        amount = transaction_data.get('amount', 0)
        transaction_type = transaction_data.get('type', 'unknown')
        user_id = transaction_data.get('user_id')
        kyc_status = transaction_data.get('kyc_completed', False)
        
        # Build query for RAG
        query = self._build_compliance_query(transaction_data)
        
        # Retrieve relevant regulations
        rag_results = self.rag.query(query, top_k=3)
        
        # Perform compliance analysis
        analysis = self._perform_compliance_check(
            transaction_data, 
            rag_results
        )
        
        # Generate structured output
        output = {
            "transaction_id": transaction_data.get('transaction_id', 'unknown'),
            "timestamp": datetime.now().isoformat(),
            "compliance_status": analysis['status'],
            "risk_score": analysis['risk_score'],
            "explanation": analysis['explanation'],
            "citations": analysis['citations'],
            "risk_decomposition": analysis['risk_decomposition'],
            "recommendations": analysis['recommendations'],
            "requires_manual_review": analysis['manual_review_required']
        }
        
        # Log analysis
        self.analysis_history.append(output)
        
        return output
    
    def _build_compliance_query(self, transaction_data: Dict) -> str:
        """Build intelligent query for RAG based on transaction"""
        amount = transaction_data.get('amount', 0)
        transaction_type = transaction_data.get('type', 'transfer')
        
        # Build context-aware query
        queries = []
        
        # Amount-based queries
        if amount > 50000:
            queries.append("high value transaction reporting requirements")
        
        # KYC-related
        if not transaction_data.get('kyc_completed'):
            queries.append("KYC verification requirements")
        
        # Transaction type specific
        if transaction_type in ['cash_deposit', 'cash_withdrawal']:
            queries.append("cash transaction limits and reporting")
        
        return " ".join(queries) if queries else "general transaction compliance"
    
    def _perform_compliance_check(self, 
                                   transaction_data: Dict, 
                                   rag_results: List[Dict]) -> Dict:
        """Perform detailed compliance analysis"""
        
        amount = transaction_data.get('amount', 0)
        kyc_status = transaction_data.get('kyc_completed', False)
        transaction_type = transaction_data.get('type', 'transfer')
        
        # Risk decomposition
        risk_decomposition = self._calculate_risk_decomposition(transaction_data)
        
        # Overall risk score
        overall_risk = sum(risk_decomposition.values()) / len(risk_decomposition)
        
        # Determine compliance status
        if overall_risk < 0.3:
            status = "APPROVED"
            explanation = "Transaction complies with all regulatory requirements."
        elif overall_risk < 0.6:
            status = "FLAGGED"
            explanation = "Transaction flagged for review due to moderate risk indicators."
        else:
            status = "REJECTED"
            explanation = "Transaction rejected due to high-risk indicators and potential non-compliance."
        
        # Extract citations from RAG results
        citations = [result['citation'] for result in rag_results if result['similarity_score'] > 0.1]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_decomposition, 
            transaction_data
        )
        
        # Detailed explanation with reasoning
        detailed_explanation = self._generate_detailed_explanation(
            transaction_data,
            risk_decomposition,
            rag_results
        )
        
        return {
            'status': status,
            'risk_score': round(overall_risk, 3),
            'explanation': detailed_explanation,
            'citations': citations,
            'risk_decomposition': risk_decomposition,
            'recommendations': recommendations,
            'manual_review_required': status == "FLAGGED"
        }
    
    def _calculate_risk_decomposition(self, transaction_data: Dict) -> Dict:
        """Calculate explainable risk decomposition
        
        Returns risk scores for:
        - AML risk
        - KYC risk
        - Policy ambiguity
        - Historical pattern
        """
        amount = transaction_data.get('amount', 0)
        kyc_status = transaction_data.get('kyc_completed', False)
        transaction_type = transaction_data.get('type', 'transfer')
        
        # AML Risk (Anti-Money Laundering)
        aml_risk = 0.0
        if amount > 100000:
            aml_risk += 0.3
        if transaction_type in ['cash_deposit', 'international_transfer']:
            aml_risk += 0.2
        if transaction_data.get('high_risk_country', False):
            aml_risk += 0.3
        aml_risk = min(aml_risk, 1.0)
        
        # KYC Risk
        kyc_risk = 0.0
        if not kyc_status:
            kyc_risk = 0.8
        elif transaction_data.get('kyc_expiry_soon', False):
            kyc_risk = 0.3
        
        # Policy Ambiguity Risk
        policy_ambiguity = 0.0
        if transaction_data.get('unusual_pattern', False):
            policy_ambiguity = 0.4
        if transaction_data.get('cross_border', False):
            policy_ambiguity += 0.2
        policy_ambiguity = min(policy_ambiguity, 1.0)
        
        # Historical Pattern Risk
        historical_risk = 0.0
        if transaction_data.get('first_transaction', False):
            historical_risk = 0.3
        if transaction_data.get('sudden_large_amount', False):
            historical_risk += 0.3
        historical_risk = min(historical_risk, 1.0)
        
        return {
            "aml_risk": round(aml_risk, 3),
            "kyc_risk": round(kyc_risk, 3),
            "policy_ambiguity": round(policy_ambiguity, 3),
            "historical_pattern": round(historical_risk, 3)
        }
    
    def _generate_recommendations(self, 
                                   risk_decomposition: Dict, 
                                   transaction_data: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if risk_decomposition['aml_risk'] > 0.5:
            recommendations.append(
                "Conduct enhanced due diligence for AML compliance"
            )
        
        if risk_decomposition['kyc_risk'] > 0.5:
            recommendations.append(
                "Complete or update KYC verification before processing"
            )
        
        if risk_decomposition['policy_ambiguity'] > 0.4:
            recommendations.append(
                "Review transaction against latest regulatory updates"
            )
        
        if risk_decomposition['historical_pattern'] > 0.4:
            recommendations.append(
                "Verify transaction pattern with customer directly"
            )
        
        if not recommendations:
            recommendations.append("Transaction appears compliant, proceed normally")
        
        return recommendations
    
    def _generate_detailed_explanation(self,
                                        transaction_data: Dict,
                                        risk_decomposition: Dict,
                                        rag_results: List[Dict]) -> str:
        """Generate human-readable explanation with citations"""
        
        explanation_parts = []
        
        # Transaction overview
        amount = transaction_data.get('amount', 0)
        explanation_parts.append(
            f"Transaction of INR {amount:,.2f} analyzed for compliance."
        )
        
        # Risk factors
        high_risk_factors = [
            factor for factor, score in risk_decomposition.items() 
            if score > 0.5
        ]
        
        if high_risk_factors:
            factors_str = ", ".join([f.replace('_', ' ').title() for f in high_risk_factors])
            explanation_parts.append(
                f"High risk indicators detected: {factors_str}."
            )
        
        # Regulatory references
        if rag_results and rag_results[0]['similarity_score'] > 0.1:
            top_result = rag_results[0]
            explanation_parts.append(
                f"According to {top_result['regulation']}, {top_result['text'][:150]}..."
            )
        
        # KYC specific
        if not transaction_data.get('kyc_completed', False):
            explanation_parts.append(
                "KYC verification is incomplete, which violates RBI guidelines for customer identification."
            )
        
        return " ".join(explanation_parts)
    
    def get_analysis_history(self, limit: int = 10) -> List[Dict]:
        """Get recent analysis history"""
        return self.analysis_history[-limit:]


# Example usage
if __name__ == "__main__":
    # Initialize RAG Pipeline
    from rag_pipeline import RAGPipeline
    
    rag = RAGPipeline()
    
    # Ingest sample regulation
    rbi_doc = """
    Section 2.2: High-Value Transaction Requirements
    For transactions exceeding INR 50,000, mandatory KYC verification is required.
    All cash transactions above INR 2,00,000 must be reported to FIU-IND within 24 hours.
    """
    
    rag.ingest_document(rbi_doc, {
        'doc_id': 'RBI_HVT_2024',
        'doc_type': 'High_Value_Transactions',
        'source': 'RBI Circular',
        'regulation': 'RBI',
        'date': '2024-01-15'
    })
    
    # Initialize Co-Pilot
    copilot = ComplianceCoPilot(rag)
    
    # Test transaction
    test_transaction = {
        'transaction_id': 'TXN001',
        'amount': 250000,
        'type': 'cash_deposit',
        'user_id': 'USER123',
        'kyc_completed': False,
        'high_risk_country': False,
        'unusual_pattern': True,
        'first_transaction': False
    }
    
    # Analyze
    result = copilot.analyze_transaction(test_transaction)
    
    # Pretty print JSON output
    print("\n" + "="*80)
    print("COMPLIANCE CO-PILOT ANALYSIS")
    print("="*80)
    print(json.dumps(result, indent=2))
