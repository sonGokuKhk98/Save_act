from supermemory import Supermemory
import os
from dotenv import load_dotenv

load_dotenv()
client = Supermemory(api_key=os.environ.get("SUPERMEMORY_API_KEY"))


# Create one rich memory about quantum computing applications
memory_content = """Quantum computing represents a paradigm shift in computational power, leveraging quantum mechanical phenomena like superposition and entanglement to solve problems that are intractable for classical computers.


The field emerged from theoretical work in the 1980s, when physicist Richard Feynman proposed that quantum systems could simulate other quantum systems more efficiently than classical computers. This insight led to the development of quantum algorithms like Shor's algorithm for factoring large numbers and Grover's algorithm for unstructured search problems.


Today, quantum computing applications span multiple domains: in cryptography, quantum computers threaten current encryption standards while enabling new quantum-resistant protocols; in drug discovery, they can simulate molecular interactions with unprecedented accuracy; in optimization problems like logistics and financial modeling, they offer exponential speedups for certain classes of problems.


Major tech companies including IBM, Google, and Microsoft have invested billions in quantum computing research, while startups like Rigetti Computing and IonQ focus on specific hardware approaches. The race for quantum advantage - demonstrating a quantum computer solving a problem faster than any classical computer - has become a key milestone in the field.


Despite the promise, significant challenges remain: quantum decoherence, error correction, and scaling qubit counts while maintaining coherence. Researchers are exploring various approaches including superconducting qubits, trapped ions, topological qubits, and photonic systems, each with different trade-offs between coherence time, gate fidelity, and scalability."""


# Add the memory to Supermemory
# response = client.memories.add(
#     content=memory_content,
#     container_tag="quantum-computing",
#     metadata={
#         "category": "technology-overview",
#         "topic": "quantum-computing",
#         "complexity": "intermediate",
#         "word_count": len(memory_content.split())
#     }
# )



# print(f"Memory added successfully!")
# print(f"Memory ID: {response.id}")
# print(f"Content length: {len(memory_content)} characters")


# results = client.search.memories(q="give me routine for skin care for melasma?", limit=3,include={"documents":True})
# print(results)

import requests

url = "https://api.supermemory.ai/v3/search"

payload = { "q": "give me routine for skin care for melasma?" ,"chunkThreshold":0.6}
headers = {
    "Authorization": "Bearer sm_8PFFHrpK7x9oKvNapkispJ_AjAIQpXivxuGJOsEiTCIDVegSpzdlbVbWwLOdLoRidQskOPsXayOoXsEEsObNCRy",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())


