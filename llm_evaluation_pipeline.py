from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import GEval
import json
import time

def main():
    start_time = time.time()

    def load_json(file_path):
        with open(file_path, "r") as file:
            return json.load(file)
        
    chat_conversation = load_json('sample-chat-conversation-02.json')
    context_vectors = load_json('sample_context_vectors-02.json')

    '''
    Since we need to evaluate  test AI answers to user queries in real-time,
    I will choose last user query as input, last AI answer as output and 
    all vectors + chat history as context to feed to geval as model based scorer
    '''

    def get_total_context(context_vectors, chat_conversation):
        turns = chat_conversation["conversation_turns"]

        # Remove last turn (last user + last AI response)
        historical_turns = turns[:-2]

        chat_history_texts = []
        for turn in historical_turns:
            role = turn["role"]
            message = turn["message"].strip()
            chat_history_texts.append(f"{role}: {message}")

        chat_history_context = "\n".join(chat_history_texts)

        vector_texts = [
            item["text"].strip()
            for item in context_vectors["data"]["vector_data"]
            if "text" in item and item["text"]
        ]

        vector_context = "\n\n".join(vector_texts)

        final_context = f"""CHAT HISTORY:\n{chat_history_context} \n\nRETRIEVED CONTEXT:\n{vector_context}""".strip()

        return final_context
    
    
    output = {
        "response_relevance_completeness": {},
        "hallucination_factual_accuracy": {}
    }

    last_user_turn = next(
        t for t in reversed(chat_conversation["conversation_turns"]) if t["role"] == "user"
    )
    last_assistant_turn = next(
        t for t in reversed(chat_conversation["conversation_turns"]) if t["role"] == "assistant"
    )

    test_case = LLMTestCase(
        input=last_user_turn["message"],
        actual_output=last_assistant_turn["message"],
        context=[get_total_context(context_vectors, chat_conversation)]
    )

    relevance_completeness_metric = GEval(
        name="Response Relevance & Completeness",
        criteria=(
            "Evaluate whether the response directly answers the query and "
            "covers all information supported by the given context."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.CONTEXT,
        ],
    )

    relevance_completeness_metric.measure(test_case)

    print("Response Relevance & Completeness score: ", relevance_completeness_metric.score)
    print("Response Relevance & Completeness reason for given score: ", relevance_completeness_metric.reason)

    output["response_relevance_completeness"]["score"] = relevance_completeness_metric.score
    output["response_relevance_completeness"]["reason"] = relevance_completeness_metric.reason

    hallucination_factual_metric = GEval(
        name="Hallucination / Factual Accuracy",
        criteria=(
            "Evaluate whether the assistant’s response contains any factual claims "
            "that are not supported by or are contradicted by the provided context."
        ),
        evaluation_params=[
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.CONTEXT,
        ],
    )

    hallucination_factual_metric.measure(test_case)

    print("Hallucination / Factual Accuracy score: ", hallucination_factual_metric.score)
    print("Hallucination / Factual Accuracy reason for given score: ", hallucination_factual_metric.reason)

    output["hallucination_factual_accuracy"]["score"] = hallucination_factual_metric.score
    output["hallucination_factual_accuracy"]["reason"] = hallucination_factual_metric.reason

    def estimate_cost(prompt_text, completion_text, model="gpt-3.5-turbo"):
        # Approximate pricing (USD per 1K tokens)
        PRICING = {
            "gpt-3.5-turbo": {
                "prompt": 0.0015 / 1000,
                "completion": 0.002 / 1000,
            },
            "gpt-4": {
                "prompt": 0.03 / 1000,
                "completion": 0.06 / 1000,
            },
        }

        pricing = PRICING.get(model, PRICING["gpt-3.5-turbo"])

        # Rough token proxy (words ≈ tokens for estimation)
        prompt_tokens = len(prompt_text.split())
        completion_tokens = len(completion_text.split())

        cost = (
            prompt_tokens * pricing["prompt"]
            + completion_tokens * pricing["completion"]
        )

        return {
            "prompt_tokens_estimate": prompt_tokens,
            "completion_tokens_estimate": completion_tokens,
            "estimated_cost_usd": round(cost, 6),
        }

    prompt_text = (test_case.input + " ".join(test_case.context))
    
    completion_text = test_case.actual_output

    cost_info = estimate_cost(prompt_text=prompt_text, completion_text=completion_text, model="gpt-3.5-turbo")
    output["cost"] = cost_info

    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000
    output["latency_ms"] = round(latency_ms, 2)

if __name__ == "__main__":
    main()