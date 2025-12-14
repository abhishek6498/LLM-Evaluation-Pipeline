# LLM Response Evaluation Pipeline

---

## Overview
This repository implements an **evaluation framework for LLM-generated conversational responses**, focusing on **reliability, grounding, latency, and cost**.

The framework evaluates multi-turn chat conversations against provided contextual knowledge using **LLM-as-a-Judge** principles inspired by **G-Eval**.

The goal is to automatically assess:
- **Response Relevance & Completeness**
- **Hallucination / Factual Accuracy**
- **Latency**
- **Cost**

The design is **system-agnostic** and does not assume a specific downstream architecture (e.g., RAG vs non-RAG), as the assignment does not explicitly define one.

---

## Input Data
The evaluation operates on two provided JSON inputs:

### 1. Conversation JSON
- Contains a multi-turn chat between a user and an assistant.
- Used to construct conversational test cases.

### 2. Context Vector JSON
- Contains text chunks fetched from a vector database for a specific user message.
- Treated as the **available supporting knowledge** for evaluation.

---

## Evaluation Metrics

### 1. Response Relevance & Completeness
Evaluates whether the assistant’s response:
- Directly addresses the user’s query (**relevance**)
- Covers all required information supported by the available context (**completeness**)

**Approach**
- The evaluation metric definition is combined with the user query to derive required semantic components.
- These components are checked against the assistant response.
- Coverage is aggregated using a rubric-based scoring system.

**Output**
- Normalized score
- Natural-language explanation describing missing or weakly covered aspects

---

### 2. Hallucination / Factual Accuracy
Evaluates whether the assistant:
- Introduces information **not supported by the provided context** (hallucination)
- Makes claims that are **factually incorrect** relative to the context

**Approach**
- Factual claims are extracted from the response.
- Each claim is checked against the available context.
- Unsupported or incorrect claims are penalized.

> **Note:** A response may be factually correct but still hallucinated if the claim is not grounded in the provided context.

**Output**
- Normalized score
- Explanation identifying unsupported or incorrect claims

---

### 3. Latency
Latency measures the **end-to-end response time** of the evaluation pipeline.

**Tracked components**
- Evaluation model inference time
- Total evaluation runtime

**Reported metrics**
- Latency in milliseconds

---

### 4. Cost
Cost is estimated based on:
- Token usage for evaluation prompts
- Per-token pricing of the evaluation LLM

**Reported metrics**
- Approximate cost per evaluation
- Can be aggregated at scale (e.g., cost per 1K conversations)

---

## Evaluation Methodology

### LLM-as-a-Judge (G-Eval Style)
The framework uses a structured **LLM-as-a-Judge** approach inspired by **G-Eval**, where:

1. Evaluation criteria are explicitly defined.
2. The query and metric definition are used to derive semantic requirements.
3. The response is checked against these requirements using the available context.
4. Scores are assigned using a clear rubric.
5. Explanations are generated for auditability.

This improves:
- Consistency
- Interpretability
- Alignment with human judgment

---

## Multi-turn Conversation Handling
- The full conversation history is preserved.
- Evaluation is performed on the **final assistant response**, using:
  - The last user query
  - The complete conversation history
  - The provided context vectors

This reflects real-world conversational AI evaluation, where users primarily care about the correctness and completeness of the final response.

---

## Example Output

```json
{
  "response_relevance_completeness": {
    "score": 4.3,
    "reason": "The response addresses the user's question and covers the main factors, but omits one detail mentioned in the context."
  },
  "hallucination_factual_accuracy": {
    "score": 3.9,
    "reason": "One claim is factually correct but not supported by the provided context."
  },
  "latency_ms": 820,
  "cost_usd": 0.0041
}
