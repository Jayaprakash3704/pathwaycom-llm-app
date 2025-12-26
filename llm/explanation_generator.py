"""
LLM Explanation Generator - Human-Readable Decision Explanations

Uses LLM to explain:
- Why an anomaly was detected
- How agents reasoned about the problem
- Why specific actions were recommended
- Expected impact and risks

This demonstrates responsible AI - making decisions explainable to humans.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime


# =============================================================================
# EXPLANATION GENERATOR
# =============================================================================

class ExplanationGenerator:
    """
    Generates human-readable explanations of agent decisions.
    
    Uses LLM to translate technical incident data into clear explanations
    for operators, managers, and stakeholders.
    """
    
    def __init__(self):
        """Initialize explanation generator."""
        self._client = None
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.base_url = os.getenv("LLM_BASE_URL")
    
    @property
    def client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("GROQ_API_KEY or OPENAI_API_KEY required")
                
                kwargs = {"api_key": api_key}
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                
                self._client = OpenAI(**kwargs)
            except Exception as e:
                print(f"[EXPLANATION] Failed to initialize LLM client: {e}")
                return None
        
        return self._client
    
    def generate_explanation(
        self,
        incident: Dict[str, Any],
        explain_reasoning: bool = True,
        explain_actions: bool = True,
        explain_impact: bool = True,
    ) -> Dict[str, str]:
        """
        Generate comprehensive explanation of an incident.
        
        Args:
            incident: Incident record dictionary
            explain_reasoning: Include reasoning explanation
            explain_actions: Include action rationale
            explain_impact: Include impact assessment
        
        Returns:
            Dictionary with explanation sections
        """
        if not self.client:
            return self._fallback_explanation(incident)
        
        explanations = {}
        
        # Build context for LLM
        context = self._build_incident_context(incident)
        
        # Generate requested explanations
        if explain_reasoning:
            explanations["reasoning"] = self._explain_reasoning(context, incident)
        
        if explain_actions:
            explanations["actions"] = self._explain_actions(context, incident)
        
        if explain_impact:
            explanations["impact"] = self._explain_impact(context, incident)
        
        # Add summary
        explanations["summary"] = self._generate_summary(incident, explanations)
        
        return explanations
    
    def _build_incident_context(self, incident: Dict[str, Any]) -> str:
        """Build context string for LLM prompt."""
        return f"""
INCIDENT DETAILS:
- ID: {incident['incident_id']}
- Type: {incident['anomaly_type']}
- Severity: {incident['severity']}/5
- Source: {incident['source']}
- Priority: {incident['priority_level']}
- Detected: {incident['detected_at']}

AGENT ANALYSIS:
- Root Cause: {incident['root_cause_analysis']}
- Impact Assessment: {incident['impact_assessment']}

RECOMMENDED ACTIONS:
{chr(10).join('- ' + action for action in incident['recommended_actions'])}

ACTIONS TAKEN:
{chr(10).join('- ' + action for action in incident['actions_taken'])}
"""
    
    def _explain_reasoning(self, context: str, incident: Dict[str, Any]) -> str:
        """Explain how agents analyzed the incident."""
        prompt = f"""You are an expert SRE explaining an automated incident response system's decision to a human operator.

{context}

Explain in 2-3 clear paragraphs:
1. WHY this was detected as an anomaly (what patterns triggered detection)
2. HOW the AI agents analyzed the root cause
3. WHAT made this incident important enough to act on

Write for a technical audience but avoid jargon. Be specific and concrete."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert SRE explaining automated incident response decisions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=500,
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"[EXPLANATION] Reasoning explanation failed: {e}")
            return "Explanation generation failed. Check logs for details."
    
    def _explain_actions(self, context: str, incident: Dict[str, Any]) -> str:
        """Explain why specific actions were chosen."""
        prompt = f"""You are an expert SRE explaining an automated incident response system's actions to a human operator.

{context}

Explain in 2-3 clear paragraphs:
1. WHY these specific actions were recommended (not others)
2. WHAT each action accomplishes
3. WHAT risks or trade-offs exist with these actions

Write for a technical audience. Be specific about cause and effect."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert SRE explaining automated response actions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=500,
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"[EXPLANATION] Action explanation failed: {e}")
            return "Explanation generation failed. Check logs for details."
    
    def _explain_impact(self, context: str, incident: Dict[str, Any]) -> str:
        """Explain the impact assessment."""
        prompt = f"""You are an expert SRE explaining an automated incident response system's impact assessment to a human operator.

{context}

Explain in 2-3 clear paragraphs:
1. WHAT systems/users are affected by this incident
2. HOW severe the impact is (business, technical, user experience)
3. WHAT happens if this is not resolved quickly

Write for a technical audience but also consider business impact."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert SRE explaining incident impact."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=500,
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"[EXPLANATION] Impact explanation failed: {e}")
            return "Explanation generation failed. Check logs for details."
    
    def _generate_summary(
        self, 
        incident: Dict[str, Any], 
        explanations: Dict[str, str]
    ) -> str:
        """Generate executive summary."""
        severity_label = {5: "CRITICAL", 4: "HIGH", 3: "MEDIUM", 2: "LOW", 1: "TRIVIAL"}
        
        summary = f"""
Incident {incident['incident_id']} - {severity_label.get(incident['severity'], 'UNKNOWN')} Severity

Source: {incident['source']}
Type: {incident['anomaly_type'].replace('_', ' ').title()}
Priority: {incident['priority_level']}

Automated agents detected an anomaly, performed root cause analysis, and executed {len(incident['actions_taken'])} response actions.

Actions Taken:
{chr(10).join('• ' + action for action in incident['actions_taken'])}

Status: {"Acknowledged" if incident.get('acknowledged_by') else "Needs Review"}
"""
        return summary.strip()
    
    def _fallback_explanation(self, incident: Dict[str, Any]) -> Dict[str, str]:
        """Fallback explanation when LLM unavailable."""
        return {
            "summary": f"Incident {incident['incident_id']} detected in {incident['source']}",
            "reasoning": "LLM explanation unavailable - check API configuration",
            "actions": f"Actions taken: {', '.join(incident['actions_taken'])}",
            "impact": incident['impact_assessment'],
        }
    
    def explain_for_stakeholder(
        self, 
        incident: Dict[str, Any],
        stakeholder_type: str = "executive"
    ) -> str:
        """
        Generate stakeholder-appropriate explanation.
        
        Args:
            incident: Incident record
            stakeholder_type: "executive", "technical", "customer"
        
        Returns:
            Tailored explanation
        """
        if not self.client:
            return self._fallback_explanation(incident)["summary"]
        
        prompts = {
            "executive": "Explain this incident for an executive (non-technical, business impact focus, 3-4 sentences):",
            "technical": "Explain this incident for a technical team lead (detailed, architecture focus, 1 paragraph):",
            "customer": "Explain this incident for external customers (what happened, what we did, customer impact, 2-3 sentences):",
        }
        
        context = self._build_incident_context(incident)
        prompt = f"{prompts.get(stakeholder_type, prompts['executive'])}\n\n{context}"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are communicating an incident to a {stakeholder_type}."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=300,
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"[EXPLANATION] Stakeholder explanation failed: {e}")
            return f"Incident {incident['incident_id']} in {incident['source']} - automated response in progress."
