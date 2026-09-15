"""
list_models.py — quick one-off helper.
Run this to see which model IDs your Groq key currently has access to,
since free-tier model availability changes over time.

Usage: python list_models.py
"""

import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
models = client.models.list()

print("Models available to your key:\n")
for m in models.data:
    print(f"  {m.id}")
