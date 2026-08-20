"""
RAG pipeline for the LawLM system.

This module:
1. Retrieves relevant court-case and Constitution passages from ChromaDB.
2. Uses the retrieved context together with the user's question to generate
   a response from the Gemini API
3. Exposes `answer_question()` as the main entry point for the backend.
"""

import os
import chromadb
from sentence_transformers import SentenceTransformer
from config import PipelineConfig
from google import genai

cfg=PipelineConfig()
model=SentenceTransformer(cfg.embedding_model)
client=chromadb.PersistentClient(path=cfg.chroma_dir)

#Assign Collections
# "legal_cases" is created by build_index.py, so it exists once the index
# has been built. "embedds_collection" (constitution text) is never created
# anywhere in this repo -- get_collection() raises if it's missing, which
# crashes this whole module on import (and therefore crashes any page that
# imports answer_question). get_or_create_collection() makes import safe;
# if you haven't separately ingested Constitution text into it, it's just
# empty and retrieve_context() returns no constitution passages for it.
legal_cases=client.get_collection(cfg.chroma_collection)
constitution=client.get_or_create_collection("embedds_collection")

"""Retrieve relevant passages from both legal sources."""
def retrieve_context(query):
    query_embedding=model.encode([query]).tolist()

    case_results=legal_cases.query(
        query_embeddings=query_embedding,
        n_results=3
    )

    constitution_results = constitution.query(
        query_embeddings=query_embedding,
        n_results=3
    )
    return{
        "cases": case_results,
        "constitution": constitution_results
    }
"""Generate a grounded legal response using Gemini."""
def generate_answer(query,context):
    # query() on an empty/sparse collection can return fewer than n_results,
    # or an empty list -- guard the [0] index instead of assuming it exists.
    case_docs = context["cases"]["documents"][0] if context["cases"]["documents"] else []
    constitution_docs = context["constitution"]["documents"][0] if context["constitution"]["documents"] else []

    prompt = f"""
You are LawLM, a legal research assistant and legal advisor specializing in Indian law.
Your job is to provide accurate, helpful, and empathetic legal information based on the user's question.

USER QUESTION:
{query}

RETRIEVED COURT CASES:
{case_docs}

RETRIEVED CONSTITUTION PROVISIONS:
{constitution_docs}

INSTRUCTIONS:

1. Be empathetic while understanding the user's question and answer the question directly.

2. Base your answers off of the retrieved court cases and Constitution provisions first,
   THEN add your own legal knowledge if necessary.

3. Clearly distinguish between:
   - Information directly supported by the retrieved sources.
   - General legal knowledge that you derive from your own sources.

4. If the retrieved sources do NOT contain enough information, use YOUR own
   general knowledge to provide a structured and accurate answer. However:
   - Do not invent cases, statutes, Articles, sections, citations, or facts.
   - Do not pretend that information from your general knowledge came from the
     retrieved sources.

5. If you are uncertain about legal facts, present it as your OWN OPINION rather than fact.

6. When discussing a Constitution Article, statute, or any legal jargon, explain
   it in simple language first and then provide the legal explanation when useful.

7. Always cite the specific Article, Act, section, or case contained in the
   sources used for your answer .

8. Be empathetic when the user's question involves a personal or stressful
   legal situation. Acknowledge the user's concern briefly before explaining
   the legal information. Do not exaggerate or make promises about the outcome.

9. Establish your role as a legal RESEARCH ASSISTANT and ADVISOR. you may establish facts and
   offer guidance, but can never act as the user's lawyer or guarantee a legal outcome.

10. Do not fabricate information simply to make the answer appear complete.

11. Structure your answer so that it is easy to understand. Use headings,
   bullet points, or numbered lists when appropriate.

12. End with a brief disclaimer when the question involves a specific personal
   legal situation: recommend that the user consult a qualified lawyer for personalized advice.

ANSWER THE USER'S QUESTION NOW.
"""

    client=genai.Client(
        api_key=os.getenv("GEMINI_API_KEY")
    )
    response=client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text, response.usage_metadata

"""Run the complete retrieval-augmented generation pipeline."""
def answer_question(query):
    context=retrieve_context(query)
    answer,usage_metadata=generate_answer(query,context)
    return answer,usage_metadata