import os
import sys

# Set default env variables for Pydantic validation before importing dependencies
os.environ.setdefault("API_KEY", "local_test_key_123")
os.environ.setdefault("GROQ_API_KEY", "dummy_groq_key")

import asyncio
import json
from app.core.dependencies import get_agent_service
from app.adapters.llm.litellm_adapter import LiteLLMAdapter
from app.domain.models.schemas import ChatContext, ChatMessage

# Load evaluation dataset from JSON file
def load_dataset() -> list:
    dataset_path = os.path.join(os.path.dirname(__file__), "eval_dataset.json")
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset file not found at {dataset_path}")
        sys.exit(1)
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)

EVAL_DATASET = load_dataset()

async def evaluate_case(case, agent, llm) -> dict:
    query = case["query"]
    expected = case["expected_action"]
    
    # Parse context and history Pydantic schemas if present in the test case
    context_data = case.get("context")
    context_obj = ChatContext(**context_data) if context_data else None
    
    history_data = case.get("history")
    history_list = [ChatMessage(**m) for m in history_data] if history_data else None
    
    # 1. Execute agent response
    response = await agent.get_response(
        user_query=query,
        history=history_list,
        context=context_obj
    )
    actual_msg = response["message"]
    actions = response["actions"]
    
    # 2. Check for expected frontend actions (deterministic check)
    action_ok = True
    if expected:
        action_ok = any(
            a.get("type") == "navigation" and a.get("target") == expected 
            for a in actions
        )
        
    # 3. Check message content semantic validity using Groq judge (LLM-as-a-judge)
    judge_prompt = f"""
    You are an impartial AI judge. Evaluate if the assistant's response satisfies the success criteria.
    
    USER QUERY: "{query}"
    ASSISTANT RESPONSE: "{actual_msg}"
    SUCCESS CRITERIA: "{case['criteria']}"
    
    Respond STRICTLY in JSON format with the following keys (no markdown formatting, no other text):
    {{
        "pass": true or false,
        "reason": "Clear explanation of why it passed or failed based on the criteria"
    }}
    """
    
    try:
        # Use Groq (via LiteLLM) to evaluate the output
        res = await llm.get_completion(
            messages=[{"role": "user", "content": judge_prompt}],
            temperature=0.0
        )
        content_text = res.choices[0].message.content.strip()
        
        # Clean potential markdown wrapping in LLM output
        if content_text.startswith("```"):
            lines = content_text.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                content_text = "\n".join(lines[1:-1]).strip()
                
        judge_res = json.loads(content_text)
        passed = judge_res.get("pass", False) and action_ok
        reason = judge_res.get("reason", "Criterios cumplidos")
        
        if not action_ok:
            reason = f"Acción de navegación esperada '{expected}' no fue disparada. " + reason
            
    except Exception as e:
        passed = False
        reason = f"Error en el LLM juez: {str(e)}"
        
    return {
        "query": query,
        "passed": passed,
        "reason": reason,
        "response": actual_msg
    }

async def main():
    if os.getenv("GROQ_API_KEY") == "dummy_groq_key" or not os.getenv("GROQ_API_KEY"):
        print("Warning: GROQ_API_KEY is not set or is dummy. Evaluation will run but LLM judge might fail.")
        
    agent = get_agent_service()
    llm = LiteLLMAdapter()
    
    print(f"Running LLM evaluation on {len(EVAL_DATASET)} test cases...")
    
    # Run tests concurrently to leverage Groq speed
    tasks = [evaluate_case(case, agent, llm) for case in EVAL_DATASET]
    results = await asyncio.gather(*tasks)
    
    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)
    success_rate = (passed_count / total_count) * 100
    
    # Format markdown report
    status_text = "PASSED" if success_rate == 100 else "FAILED"
    
    markdown_report = f"""## Reporte de LLM Evaluation

**Estado del Test:** {status_text}
**Tasa de Éxito:** `{passed_count}/{total_count} ({success_rate:.1f}%)`

| Pregunta | Estado | Razón / Detalle |
| :--- | :---: | :--- |
"""
    for r in results:
        status_icon = "PASS" if r["passed"] else "FAIL"
        markdown_report += f"| `{r['query']}` | {status_icon} | {r['reason']} |\n"
        
    # Write report file for PR comment integration
    report_path = "eval_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(markdown_report)
        
    print(f"\nEvaluation finished. Rate: {passed_count}/{total_count} ({success_rate:.1f}%)")
    print(f"Report saved to {report_path}")
    
    # Exit with code 1 if any case failed, triggering CI failure
    if passed_count < total_count:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
