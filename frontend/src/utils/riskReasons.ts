/**
 * Human-friendly mappings for risk tags displayed in the UI.
 * Maps raw risk tags from backend to user-friendly explanations.
 */

export const RISK_REASON_MAP: Record<string, string> = {
  HIGH_AMOUNT_NO_KYC: "Transaction amount exceeds allowed threshold and KYC is missing or incomplete.",
  SUSPICIOUS_PAYEE: "Beneficiary is on a watchlist or matches a sanctions list.",
  HIGH_FREQ_DEBIT: "High frequency of debit transactions in a short time window.",
  OFFSHORE_TRANSFER: "Transfer to a high-risk offshore jurisdiction or shell company.",
  STRUCTURING: "Transaction pattern suggests structuring to avoid reporting thresholds.",
  SANCTIONED_ENTITY: "Counterparty matches a sanctioned entity list.",
  HIGH_RISK_JURISDICTION: "Transaction involves a high-risk geographic region.",
  PEP_TRANSACTION: "Transaction involves a Politically Exposed Person.",
  LARGE_CASH_DEPOSIT: "Large cash deposit that may require additional reporting.",
  ROUND_AMOUNT: "Unusual round amount pattern detected.",
  RAPID_SUCCESSION: "Multiple transactions in rapid succession.",
  // Add additional mappings used by backend here
};

/**
 * Get a human-readable explanation for a risk tag.
 * @param riskTag - The raw risk tag from the backend
 * @returns Human-friendly explanation or the original tag if no mapping exists
 */
export function getReadableRiskReason(riskTag: string): string {
  return RISK_REASON_MAP[riskTag] || riskTag;
}

/**
 * Get human-readable explanations for multiple risk tags.
 * @param riskTags - Array of raw risk tags from the backend
 * @returns Array of human-friendly explanations
 */
export function getReadableRiskReasons(riskTags: string[] | undefined): string[] {
  if (!riskTags || !Array.isArray(riskTags)) {
    return [];
  }
  return riskTags.map(tag => getReadableRiskReason(tag));
}
