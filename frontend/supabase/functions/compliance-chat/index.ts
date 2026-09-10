import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

const SYSTEM_PROMPT = `You are PolicyGuard's AI Compliance Assistant, an expert in financial compliance, regulations, and risk management. You specialize in:

1. **KYC (Know Your Customer)**:
   - Customer identification and verification requirements
   - Enhanced due diligence for high-risk customers
   - Beneficial ownership identification
   - Customer risk profiling and categorization
   - Ongoing monitoring and periodic reviews

2. **AML (Anti-Money Laundering)**:
   - Suspicious transaction identification and reporting (STRs)
   - Transaction monitoring thresholds and patterns
   - Red flags for money laundering activities
   - Sanctions screening and compliance
   - Correspondent banking due diligence

3. **Regulatory Frameworks**:
   - RBI (Reserve Bank of India) Master Directions on KYC
   - PMLA (Prevention of Money Laundering Act)
   - FATF recommendations and guidelines
   - OFAC sanctions compliance
   - International regulatory standards

4. **Transaction Risk Assessment**:
   - High-risk jurisdiction identification
   - Unusual transaction pattern detection
   - Shell company and beneficial ownership risks
   - PEP (Politically Exposed Person) screening
   - Source of funds verification

5. **Compliance Policies**:
   - Policy documentation and updates
   - Compliance program implementation
   - Audit trail and record-keeping requirements
   - Staff training and awareness
   - Regulatory reporting obligations

When responding:
- Provide accurate, practical guidance based on current regulations
- Reference specific regulatory sections when applicable
- Explain risk factors and their implications
- Suggest actionable compliance steps
- Flag when professional legal/compliance advice should be sought
- Keep responses clear and structured

If asked about a specific transaction, analyze the risk factors and provide a balanced assessment. Always prioritize regulatory compliance and risk mitigation.`;

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { messages } = await req.json();
    
    if (!messages || !Array.isArray(messages)) {
      return new Response(
        JSON.stringify({ error: "Messages array is required" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const LOVABLE_API_KEY = Deno.env.get("LOVABLE_API_KEY");
    if (!LOVABLE_API_KEY) {
      console.error("LOVABLE_API_KEY is not configured");
      throw new Error("LOVABLE_API_KEY is not configured");
    }

    console.log("Sending request to Lovable AI Gateway...");
    console.log("Messages count:", messages.length);

    const response = await fetch("https://ai.gateway.lovable.dev/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${LOVABLE_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "google/gemini-flash-latest",
        messages: [
          { role: "system", content: SYSTEM_PROMPT },
          ...messages,
        ],
        stream: true,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("AI gateway error:", response.status, errorText);

      if (response.status === 429) {
        return new Response(
          JSON.stringify({ error: "Rate limit exceeded. Please try again in a moment." }),
          { status: 429, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }

      if (response.status === 402) {
        return new Response(
          JSON.stringify({ error: "AI usage limit reached. Please add credits to continue." }),
          { status: 402, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }

      return new Response(
        JSON.stringify({ error: "AI service temporarily unavailable" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    console.log("Streaming response from AI gateway...");

    // Return the streaming response
    return new Response(response.body, {
      headers: {
        ...corsHeaders,
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });
  } catch (error) {
    console.error("Compliance chat error:", error);
    return new Response(
      JSON.stringify({ 
        error: error instanceof Error ? error.message : "An unexpected error occurred" 
      }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
