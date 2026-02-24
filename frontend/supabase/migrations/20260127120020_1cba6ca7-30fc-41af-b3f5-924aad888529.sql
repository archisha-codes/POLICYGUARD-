-- Create transaction status enum
CREATE TYPE public.transaction_status AS ENUM ('approved', 'flagged', 'pending', 'rejected');

-- Create transactions table
CREATE TABLE public.transactions (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  transaction_id TEXT NOT NULL UNIQUE,
  customer_name TEXT NOT NULL,
  customer_id TEXT NOT NULL,
  amount DECIMAL(15,2) NOT NULL,
  currency TEXT NOT NULL DEFAULT 'USD',
  transaction_type TEXT NOT NULL,
  status public.transaction_status NOT NULL DEFAULT 'pending',
  risk_score INTEGER NOT NULL DEFAULT 0 CHECK (risk_score >= 0 AND risk_score <= 100),
  country TEXT,
  merchant TEXT,
  description TEXT,
  flagged_reasons TEXT[],
  ai_explanation TEXT,
  reviewed_by UUID REFERENCES auth.users(id),
  reviewed_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;

-- Create policies - all authenticated users can view transactions
CREATE POLICY "Authenticated users can view transactions"
  ON public.transactions FOR SELECT
  USING (auth.uid() IS NOT NULL);

-- Only admins and compliance officers can update transactions
CREATE POLICY "Admins and compliance officers can update transactions"
  ON public.transactions FOR UPDATE
  USING (
    has_role(auth.uid(), 'admin') OR 
    has_role(auth.uid(), 'compliance_officer')
  );

-- Only admins can insert transactions (typically done via system)
CREATE POLICY "Admins can insert transactions"
  ON public.transactions FOR INSERT
  WITH CHECK (has_role(auth.uid(), 'admin'));

-- Only admins can delete transactions
CREATE POLICY "Only admins can delete transactions"
  ON public.transactions FOR DELETE
  USING (has_role(auth.uid(), 'admin'));

-- Create trigger for updated_at
CREATE TRIGGER update_transactions_updated_at
  BEFORE UPDATE ON public.transactions
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

-- Insert sample transaction data
INSERT INTO public.transactions (transaction_id, customer_name, customer_id, amount, currency, transaction_type, status, risk_score, country, merchant, description, flagged_reasons, ai_explanation) VALUES
  ('TXN-001-2024', 'John Smith', 'CUST-001', 15000.00, 'USD', 'Wire Transfer', 'flagged', 85, 'Cayman Islands', 'Offshore Holdings Ltd', 'International wire transfer to offshore account', ARRAY['High-risk jurisdiction', 'Large amount', 'New beneficiary'], 'This transaction exhibits multiple risk indicators: destination is a known tax haven, amount exceeds normal customer pattern, and beneficiary account was recently created.'),
  ('TXN-002-2024', 'Sarah Johnson', 'CUST-002', 2500.00, 'USD', 'ACH Transfer', 'approved', 15, 'United States', 'Amazon Inc', 'Regular vendor payment', NULL, 'Transaction matches established customer pattern. Vendor is verified and on approved list.'),
  ('TXN-003-2024', 'Michael Chen', 'CUST-003', 50000.00, 'EUR', 'SWIFT Transfer', 'pending', 62, 'Switzerland', 'Swiss Private Bank', 'Investment account funding', ARRAY['Large amount', 'First-time destination'], 'Elevated risk due to transaction size and new destination. Customer has verified source of funds documentation on file.'),
  ('TXN-004-2024', 'Emma Williams', 'CUST-004', 890.00, 'USD', 'Card Payment', 'approved', 8, 'United States', 'Whole Foods Market', 'Grocery purchase', NULL, 'Low-risk retail transaction within normal spending pattern.'),
  ('TXN-005-2024', 'Robert Davis', 'CUST-005', 125000.00, 'USD', 'Wire Transfer', 'rejected', 95, 'Russia', 'Unknown Entity', 'Business payment', ARRAY['Sanctioned country', 'Unknown beneficiary', 'Unusual pattern'], 'Transaction blocked: Destination country under OFAC sanctions. Beneficiary entity not found in any business registry.'),
  ('TXN-006-2024', 'Lisa Anderson', 'CUST-006', 3200.00, 'GBP', 'SEPA Transfer', 'approved', 22, 'United Kingdom', 'Harrods Ltd', 'Retail purchase', NULL, 'Verified merchant, transaction within customer limits.'),
  ('TXN-007-2024', 'David Martinez', 'CUST-007', 75000.00, 'USD', 'Wire Transfer', 'flagged', 78, 'Panama', 'Central American Trading Co', 'Trade finance payment', ARRAY['High-risk jurisdiction', 'Shell company indicators'], 'Beneficiary shows characteristics of shell company. Recommend enhanced due diligence before approval.'),
  ('TXN-008-2024', 'Jennifer Brown', 'CUST-008', 1500.00, 'USD', 'ACH Transfer', 'pending', 35, 'United States', 'Local Contractor LLC', 'Service payment', ARRAY['New payee'], 'First payment to this vendor. Basic verification pending.'),
  ('TXN-009-2024', 'James Wilson', 'CUST-009', 8900.00, 'USD', 'Wire Transfer', 'approved', 28, 'Canada', 'Toronto Holdings Inc', 'Investment dividend', NULL, 'Recurring dividend payment from verified investment account.'),
  ('TXN-010-2024', 'Maria Garcia', 'CUST-010', 45000.00, 'USD', 'SWIFT Transfer', 'flagged', 71, 'Cyprus', 'Mediterranean Ventures', 'Business acquisition', ARRAY['Unusual amount', 'Complex structure'], 'Transaction structure shows layering characteristics. Multiple intermediate accounts detected.');