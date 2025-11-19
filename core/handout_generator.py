from typing import List, Dict
from groq import Groq
import streamlit as st


def build_handout_prompt(visitor_context: Dict, services: List[Dict]) -> str:
    context_str = (
        f"Visitor context: age_group={visitor_context['age_group']}, "
        f"language={visitor_context['language']}, "
        f"needs={', '.join(visitor_context['needs'])}, "
        f"housing_status={visitor_context.get('housing_status', 'unknown')}.\n\n"
    )

    services_str = "Relevant services:\n"
    for i, svc in enumerate(services, start=1):
        services_str += (
            f"{i}. {svc['name']} – {svc['description']} "
            f"Hours today: {svc['hours_today']}. "
            f"Address: {svc['address']}. "
            f"Eligibility: {svc['eligibility']}.\n"
        )

    instructions = """
You are helping a front-line worker at an Indigenous community centre
write a simple, kind handout about local services.

Write in clear, plain English (around grade 6 reading level).
Steps:
1. Start with one short sentence that reassures the visitor.
2. Then list each service with:
   - What it offers
   - When to go (today)
   - Where it is
3. Use short sentences and bullet points.
4. End by saying they can come back to the centre if they need help.

Do not invent services that are not listed.
"""

    return context_str + services_str + "\n" + instructions


def generate_handout(visitor_context: Dict, services: List[Dict]) -> str:
    """
    Calls the LLM to generate the handout text.
    """

    prompt = build_handout_prompt(visitor_context, services)

    # Read API key from Streamlit secrets
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        return "Error: GROQ_API_KEY is not set in Streamlit secrets."

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "system",
            "content": "You write clear, friendly, low-literacy handouts."
        },
        {
            "role": "user",
            "content": prompt
        },
    ],
    temperature=0.4,
    max_tokens=600,
)


    handout_text = response.choices[0].message.content
    return handout_text
