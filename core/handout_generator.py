# core/handout_generator.py

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

    services_str = "Relevant services (with raw data from the tool):\n"
    for i, svc in enumerate(services, start=1):
        services_str += (
            f"{i}. name={svc['name']} | "
            f"description={svc['description']} | "
            f"hours_today={svc['hours_today']} | "
            f"address={svc['address']} | "
            f"eligibility={svc['eligibility']}\n"
        )

    instructions = """
You are helping a front-line worker at an Indigenous community centre
write a simple, kind handout about local services.

Write in clear, plain English (around grade 6 reading level).

IMPORTANT RULES:

1. Reassurance opening
   - Start with ONE short sentence that welcomes and reassures the visitor.

2. Cards per service
   - Then, for each service, write a small "card" in this structure:

     [emoji] Service name
     • What it offers (1–2 short lines)
     • When to go TODAY (use the hours_today field)
     • Where: a street-style address with a number
     • Who it is for / eligibility (if important)

   - Put a blank line between cards so they look like separate boxes.

3. Emoji use
   - Start each service card with an emoji that roughly matches the service, for example:
       Food = 🍽️
       Health & Wellness = 🩺
       Mental Health = 🧠
       Housing & Shelter = 🏠
       Clothes & Hygiene = 🧥
       Work / Employment = 💼
       Family & Children = 👨‍👩‍👧
       Culture / Community = 🌿
   - If you are not sure, use a neutral emoji like ⭐.

4. Address rule (VERY IMPORTANT)
   - Use the address field from the data when possible.
   - If the address does NOT include a street number (like "123"), then
     INVENT a simple, generic one so it looks like a complete address,
     e.g. change "Main Street" into "123 Main Street".
   - Do NOT invent apartment numbers, building names, or people names.
   - The address only needs to *look* like a real address. It must NOT identify anyone.

5. Safety and tone
   - Use short sentences.
   - Be warm but not childish.
   - Never add personal details about the visitor.

6. Closing line
   - End with one short sentence like:
     "You can always come back to the centre if you need more help."
"""

    return context_str + services_str + "\n" + instructions
