import os
import json
from dotenv import load_dotenv
import streamlit as st
from openai import AzureOpenAI
from search_functions import (
    search_testportfolio,
    search_sample_logistic,
    search_turnaround_times,
    search_containers,
    get_database_schema,
    find_cas_number,
    search_similar_parameters,
    # Keyword/Filter lookup functions (exact code matching)
    lookup_logistics_by_testcode,
    lookup_tat_by_testcode,
    lookup_container_by_code,
    lookup_testportfolio_by_code,
    # Bottle optimization function
    get_container_requirements_for_tests
)
from tools_schema import TOOLS

# =============================
# CONFIG
# =============================

# Load from .env for local development
load_dotenv("azure.env")

def get_secret(key: str) -> str:
    """Get secret from Streamlit Cloud secrets or environment variables."""
    # Try Streamlit secrets first (for cloud deployment)
    if hasattr(st, 'secrets') and key in st.secrets:
        return st.secrets[key]
    # Fall back to environment variables (for local development)
    return os.getenv(key)

AZURE_MODEL_4 = get_secret("AZURE_OPENAI_MODEL_4")
AZURE_ENDPOINT_4 = get_secret("AZURE_OPENAI_ENDPOINT_4")
AZURE_KEY_4 = get_secret("AZURE_OPENAI_API_KEY_4")
AZURE_API_VERSION_4 = get_secret("AZURE_OPENAI_API_VERSION_4")
AZURE_MODEL_5 = get_secret("AZURE_OPENAI_MODEL_5")
AZURE_ENDPOINT_5 = get_secret("AZURE_OPENAI_ENDPOINT_5")
AZURE_KEY_5 = get_secret("AZURE_OPENAI_API_KEY_5")
AZURE_API_VERSION_5 = get_secret("AZURE_OPENAI_API_VERSION_5")
def get_client(model: str) -> AzureOpenAI:
    if model == AZURE_MODEL_5:
        return AzureOpenAI(
            azure_endpoint=AZURE_ENDPOINT_5,
            api_key=AZURE_KEY_5,
            api_version=AZURE_API_VERSION_5
        )
    return AzureOpenAI(
        azure_endpoint=AZURE_ENDPOINT_4,
        api_key=AZURE_KEY_4,
        api_version=AZURE_API_VERSION_4
    )

SYSTEM_PROMPT = """
You are a knowledgeable and professional laboratory assistant for Eurofins.
You help customers and internal staff with questions about lab tests, analyses,
sample requirements, turnaround times, and detection limits.

## TOOL CALL ORDER (FOLLOW THIS SEQUENCE)

### STEP 1: PARAMETER VALIDATION (when user mentions a parameter/test name)
- **search_similar_parameters(search_term)**: Find exact or similar parameter/test names with available matrices
  → If exact match found with user's matrix → proceed to Step 2
  → If parameter not available with requested matrix → show available matrices and ask user which to proceed with
  → If no match → show similar options and ask user to confirm

### STEP 2: GET TEST CODE (after parameter is confirmed)
- **search_testportfolio(search_query)**: Search by confirmed parameter name + matrix
  → Returns: Test Code, parameter name, LOD, LOQ, reporting limits, units, methods
  → This is the MASTER TABLE - get Test Code here first

### STEP 3: USE LOOKUP TOOLS (with Test Code from Step 2)
- **lookup_logistics_by_testcode(test_code)**: Containers, quantities, preservation
- **lookup_tat_by_testcode(test_code)**: TAT, rush options, performer
- **lookup_container_by_code(container_code)**: Barcode prefix, ordering info
- **lookup_testportfolio_by_code(code, code_type)**: Exact Test Code or CAS number lookup

### OPTIONAL: SCHEMA TOOL
- **get_database_schema()**: Returns ALL 4 table schemas with sample records
  → Call when you need to understand database structure or field names
  → Useful at conversation start or when searches return no results

## BOTTLE/CONTAINER QUESTIONS - TWO TYPES

**Type 1 - WHICH containers:** "What bottles for X, Y, Z?" or "Which container do I need for [parameter]?"
→ Use CONTAINER IDENTIFICATION workflow below
→ Returns container barcode prefixes (e.g., "Parameter X: bottle 067")

**Type 2 - HOW MANY containers:** "How many bottles do I need for X, Y, Z?" or "Can these tests share?"
→ Use BOTTLE COUNT OPTIMIZATION workflow below
→ Returns bottle count with sharing info (e.g., "2 bottles needed, tests A and B can share")

IMPORTANT: Distinguish between these question types and use the appropriate workflow.

---

## CONTAINER IDENTIFICATION (Which bottles for parameters?)

When user asks "What bottles/containers for X, Y, Z?" or "Which container do I need?":

### WORKFLOW:
1. search_similar_parameters for EACH parameter
2. For EACH result, find test_code matching user's matrix
3. lookup_logistics_by_testcode(test_code) → get Preferred Container Code
4. lookup_container_by_code(container_code) → get TSC Main Barcode Prefix
5. Present results using BARCODE PREFIX (067, 080, etc.) not internal codes

### MULTIPLE TEST CODES:
- If multiple test codes remain after matrix filtering:
  - If ≤5 options → show all with their container barcode prefixes
  - If >5 options → ask customer for clarification
- Different test codes may require different containers

### OUTPUT FORMAT:
Present results grouped by parameter with barcode prefix:
- "[Parameter A]: bottle [barcode prefix]"
- "[Parameter B and C]: bottle [barcode prefix]"

---

## BOTTLE COUNT OPTIMIZATION (How many bottles needed?)

When user asks "How many bottles do I need?" or about sharing containers:

### WORKFLOW:
1. Call search_similar_parameters for EACH parameter to get test_codes
   - Example: search_similar_parameters("iron") → test_codes: ["F1068"]
2. Collect all test_codes from results into a list
3. Call get_container_requirements_for_tests(test_codes, matrix)
4. Interpret and explain results to user

### RESULT INTERPRETATION:
- **can_share=true**: "Tests X, Y can share 1 bottle (container [name])"
- **can_share=false**: "Tests X and Y need separate bottles because [reason]"
- **bottles_saved**: Highlight optimization benefit: "Sharing saves N bottles"

### SHARING RULES (for context):
- Tests can share IF: same AMT code + same container name + "Shareable if same AMT" rule
- Tests CANNOT share IF: different AMT codes, different containers, or "Not shareable" rule
- Combined sample volume must fit in container capacity

### EXPLAIN TO USER:
- Which tests can share and why (same analytical method)
- Total bottles needed with sharing vs without
- Volume requirements per container

### WHY USE LOOKUP TOOLS INSTEAD OF SEMANTIC SEARCH?
Semantic search + code + matrix text can return WRONG results:
- Search: "FF1Q2 groundwater" may return ci_code = "PF185" (WRONG!)
- Reason: "groundwater" matches content fields, code is ignored

Lookup tools use exact keyword matching:
- lookup_logistics_by_testcode("FF1Q2") → returns ALL rows where ci_code = "FF1Q2" exactly

## UNDERSTANDING USER QUESTIONS
Users will not always ask in a structured or technical way. Questions may
arrive as casual conversation, long emails, or multi-part requests.
Regardless of format, always scan the message and extract:
- Any parameter or substance name, even if mentioned casually
- Any matrix or sample type, even if described informally
- Any test code mentioned directly or indirectly
- Any reference to containers, bottles, or sample requirements
- Any reference to limits, results, or values on a report
- Any reference to time, speed, or urgency
- Any question about combining or sharing tests or containers

Once you identify the key technical elements, always search the index
using those elements. If the message contains multiple questions,
extract and search each one separately before composing your response.

## MANDATORY TOOL USAGE
Always call the appropriate search tool before answering any technical question.
Never answer from your own knowledge when the question involves parameters,
test codes, containers, limits, turnaround times, sample quantities,
preservation, or method comparisons. This applies regardless of how the
question is phrased. Always retrieve first, then answer.

### STRICT MULTI-ANALYSIS TOOL CALL RULE
If a user message contains multiple parameters, test codes, or matrices:
- You MUST decompose them into separate logical analyses.
- You MUST call the relevant tool once per analysis.
- Each tool call must contain only ONE test code OR one parameter–matrix combination.
- NEVER combine multiple analyses into a single search_query.
- NEVER merge multiple test codes into one tool call.

## ABBREVIATION HANDLING
When user provides abbreviations:
- Use your chemistry and laboratory knowledge to interpret them
- If uncertain, state your interpretation and ask user to confirm before searching
- Distinguish between TEST NAME (group analysis) vs PARAMETER NAME (specific substance)

## TABLE RELATIONSHIPS
- Test Code (Table 1) = CI Code (Table 2) = Test Code (Table 3)
- Preferred Type of Sample Container code (Table 2) = TSC code (Table 4)
- Matrix Code links Tables 1, 2, and 3

## NEVER DO THIS
- ❌ Skip parameter validation — always call search_similar_parameters first for parameter questions
- ❌ Use semantic search with Test Code + matrix text — use lookup tools instead
- ❌ Skip Table 1 and go directly to Table 2 or Table 3
- ❌ Guess test codes — always retrieve them from search_testportfolio

## MIXED QUERY RULE — NON-NEGOTIABLE
Some user messages combine elements that tools cannot answer (report numbers
like AR-421-..., footnote explanations, invoice questions) with elements that
tools CAN and MUST answer (test codes like F2365, parameter names like sulfate
or chromium, container questions, method comparisons).

The presence of unanswerable elements NEVER exempts you from calling tools
for the answerable elements.

MANDATORY decomposition for every message:
1. Scan the full message and list every technical element present
2. For parameter names → follow TOOL CALL ORDER (search_similar_parameters → search_testportfolio → lookup tools)
3. For test codes (F-codes) → search_testportfolio directly
4. Call the appropriate tool for EACH technical element found
5. Compose response using retrieved data; for non-tool parts, use general knowledge clearly labeled as such

## SPECIFIC RULES

**CAS Number Search:** If search_testportfolio returns a DIFFERENT parameter than what user asked:
1. Call find_cas_number with user's original parameter name
2. If CAS found → search test_portfolio again using CAS number
3. If CAS "UNKNOWN" → inform user parameter could not be identified
4. NEVER answer with data from a different parameter than requested

**Matrix Matching:**
- Match user's matrix to the correct Matrix Case in results
- Matrix names contain regulation details (e.g., "Ground water: regulation is RvA")
- If no match → fall back to Default Case / N/A rows and inform user
- If ambiguous → state your assumption and offer to refine

**Detection Limits:**
- Detection limits are in the LOQ column (not LOD)
- Format: LOQ value + units (e.g., "20 mg/kg ds" or "2 mg/L")
- If LOQ is NULL → use Reporting Limit and state this clearly

**Container Barcode Prefix:**
- ALWAYS use TSC Main Barcode Prefix (067, 062, 080) in customer responses
- NEVER use internal codes (CS012, T0004, COMPA) in customer-facing responses
- Format: "For VOCl: use bottle 067"

**Response Formatting:**
- Include test code, units, and matrix context in answers
- Use tables for multiple parameters or comparisons
- Provide summary section for complex responses

## WHEN RETRIEVED DATA DOES NOT MATCH THE QUESTION
After calling the tools, results may not always fully match what the user
is asking. In these cases, always be transparent:
- **No results found**: Inform the user clearly that the parameter, test,
  or combination could not be found and recommend contacting the lab directly.
- **Partial match**: State what was found and what could not be confirmed.
  If a Default Case fallback was used, mention this explicitly.
- **Report or order references** (e.g., AR-421-2025-084798-01): These are
  not stored in the system. Direct the user to the lab or account manager.
- **Pricing, invoices, or commercial agreements**: Not available in the tools.
  Direct the user to their account manager or commercial team.
- **Actual measured results from a report**: This system only holds reference
  data such as standard limits, methods, and containers — not sample results.
  Clearly distinguish between reference data and actual lab report values.

Always be honest about the boundaries of what the system can answer.
A clear "this information is not available here, please contact the lab"
is always better than an answer based on incomplete or mismatched data.

## HANDLING QUESTIONS OUTSIDE THE TOOLS
Some questions involve lab processing concepts or analytical explanations
beyond what the tools retrieve (e.g., why dry weight affects a reporting
limit, what a footnote means). In these cases:
- First retrieve all relevant data from the tools.
- Then supplement with a general explanation based on laboratory knowledge.
- Always distinguish between retrieved data and general explanation.
- If entirely outside the scope of the tools, recommend contacting the lab.
# TOOL CALL EFFICIENCY

You can make up to 35 tool calls per question to gather comprehensive information.
However, be strategic:
- Break complex multi-part questions into focused searches
- Prioritize the most critical information first
- Avoid redundant searches for the same parameter/matrix combination
- If a question has 5+ parameters, focus on the most relevant ones first
- Balance thoroughness with response time — don't exhaust all 35 calls unless necessary

If you approach the limit, synthesize what you have collected rather than continuing to search.
## TONE AND STYLE
- Professional, concise, and precise at all times.
- Never expose raw API responses, internal codes, or system errors to the user.
- Structure responses clearly, especially for multi-question messages.
- Do not guess or fabricate values — every technical value must come
  from a tool result.

**I repeat , Do not assume any information based on your prior knowledge. Carefully read and understand each question. Identify the relevant parameters strictly based on the available tool details. Then, call the appropriate tools to retrieve the correct and relevant results.**
"""


# =============================
# TOOL REGISTRY
# =============================

# Tools that accept top_results parameter
SEARCH_TOOLS = {
    "search_testportfolio": search_testportfolio,
    "search_sample_logistic": search_sample_logistic,
    "search_turnaround_times": search_turnaround_times,
    "search_containers": search_containers,
}

# Tools that don't need top_results parameter
SIMPLE_TOOLS = {
    "get_database_schema": get_database_schema,
    "find_cas_number": find_cas_number,
    "search_similar_parameters": search_similar_parameters,
    "lookup_logistics_by_testcode": lookup_logistics_by_testcode,
    "lookup_tat_by_testcode": lookup_tat_by_testcode,
    "lookup_container_by_code": lookup_container_by_code,
    "lookup_testportfolio_by_code": lookup_testportfolio_by_code,
    "get_container_requirements_for_tests": get_container_requirements_for_tests,
}

# =============================
# AGENT LOOP
# =============================

def run_agent(messages: list, status_container,max_tool_calls: int = 35,model: str = None, top_results: int = 1) -> str:
    client = get_client(model)
    tool_call_count = 0
    is_first_call = True
    completion_args = {
    "model": model,
    "messages": messages,
    "tools": TOOLS,
    "parallel_tool_calls": False,

}
    if model != AZURE_MODEL_5:
        completion_args["temperature"] = 0
    else:
        completion_args["temperature"] = 0
        # Use reasoning_effort for GPT-5.2 instead of temperature
        completion_args["parallel_tool_calls"]=True
    while True:
        if is_first_call:
            injected_messages = messages + [
                {
                    "role": "system",
                       "content": (
        "FIRST TOOL CALL REQUIREMENT:\n"
        "If this is the start of a new conversation OR if the user asks about parameters/tests you haven't seen, "
        "your FIRST tool call MUST be get_database_schema() to understand the complete database structure.\n\n"
        "TWO-PHASE WORKFLOW (MANDATORY):\n"
        "PHASE 1 - DISCOVERY: Use search_testportfolio to get Test Code from parameter name/abbreviation\n"
        "PHASE 2 - LOOKUP: Use lookup tools with exact Test Code for guaranteed matching:\n"
        "  - lookup_logistics_by_testcode(test_code) for containers, quantities, preservation\n"
        "  - lookup_tat_by_testcode(test_code) for TAT, rush options\n"
        "  - lookup_container_by_code(container_code) for barcode prefix, ordering info\n\n"
        "WHY LOOKUP TOOLS: Semantic search with 'FF1Q2 groundwater' may return wrong ci_code='PF185'.\n"
        "Lookup tools search ONLY the code field = exact match guaranteed.\n\n"
        "ABBREVIATION HANDLING:\n"
        "When user provides abbreviations, confirm your interpretation with the user BEFORE searching.\n\n"
        "CRITICAL RULES:\n"
        "- NEVER skip search_testportfolio — it is the MASTER TABLE\n"
        "- Use LOOKUP tools (not semantic search) when you have an exact Test Code\n"
        "- Never combine multiple parameters or test codes in one tool call\n"
        "- Never answer technical questions from your own knowledge\n"
        "- Always retrieve data first, then answer"
    )
                }
            ]
            completion_args["messages"] = injected_messages
        else:
            completion_args["messages"] = messages
        # Step 1 — Call the LLM
        response = client.chat.completions.create(**completion_args)

        message = response.choices[0].message
        is_first_call = False
        # Step 2 — Check if LLM wants to call a tool
        if message.tool_calls:
             # Check if we've exceeded the limit
            if tool_call_count >= max_tool_calls:
                
                # Add instruction to answer with collected data
                messages.append({
                    "role": "system",
                    "content": (
                        f"IMPORTANT: Maximum tool call limit ({max_tool_calls}) reached. "
                        "You have searched the database extensively and collected information "
                        "from multiple queries. Now answer the user's question using ALL the "
                        "information you have gathered. Do NOT request any more tool calls. "
                        "If information is incomplete, clearly state what is available and "
                        "what is missing, then suggest next steps for the user."
                    )
                })
                
                
                # Show warning in UI
                with status_container:
                    st.warning(
                        f"⚠️ Search limit reached ({max_tool_calls} searches completed). "
                        "Generating answer with collected information..."
                    )
                
                # Continue loop - LLM will now respond without tools
                continue

            # Step 3 — Loop through each tool call
            for tool_call in message.tool_calls:
                tool_call_count += 1
                function_name = tool_call.function.name
                arguments     = json.loads(tool_call.function.arguments)

                # Step 4 — Show tool call status in UI
                with status_container:
                    with st.status(
                        f"🔧 Calling: **{function_name}**",
                        expanded=False,
                        state="running"
                    ) as status:

                        st.write("**Search query:**")
                        st.json(arguments)

                        # Step 5 — Execute the matching function using registry
                        if function_name in SEARCH_TOOLS:
                            # Search tools with top_results parameter
                            tool_result = SEARCH_TOOLS[function_name](**arguments, top=top_results)
                        elif function_name in SIMPLE_TOOLS:
                            # Simple tools without top_results
                            tool_result = SIMPLE_TOOLS[function_name](**arguments)
                        else:
                            tool_result = f"Unknown tool: {function_name}"

                        # Step 6 — Serialize result
                        tool_result_str = json.dumps(tool_result, default=str)

                        # Step 7 — Show result inside dropdown
                        st.write("**Result:**")
                        st.json(json.loads(tool_result_str))

                        # Step 8 — Update status to complete
                        status.update(
                            label=f"✅ Completed: **{function_name}**",
                            state="complete",
                            expanded=False
                        )

                # Step 9 — Append assistant tool call to messages
                messages.append({
                    "role": "assistant",
                    "tool_calls": [tool_call],
                    "content": None
                })

                # Step 10 — Append tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result_str
                })

            # Step 11 — Loop back to LLM with updated messages
            continue

        # Step 12 — No tool calls — LLM gives final answer
        else:
            final_answer = message.content
            messages.append({
                "role": "assistant",
                "content": final_answer
            })
            return final_answer


# =============================
# STREAMLIT UI
# =============================

def main():
    st.set_page_config(
        page_title="Eurofins Lab Assistant",
        page_icon="🧪",
        layout="centered"
    )

    st.title("🧪 Eurofins Lab Assistant")
    st.caption("Powered by Azure OpenAI")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if not st.session_state.messages:
        st.session_state.is_processing = False

    # Display full chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input — disabled while processing
    if prompt := st.chat_input(
        "Ask me anything about Eurofins lab tests...",
        disabled=st.session_state.is_processing
    ):
        # Lock input while processing
        st.session_state.is_processing = True

        # Display and store user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Build full message list for agent including history
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in st.session_state.messages:
            if msg["role"] in ["user", "assistant"]:
                messages.append(msg)

        # Get and display assistant response
        with st.chat_message("assistant"):
            status_container = st.container()
            response_placeholder = st.empty()

            try:
                answer = run_agent(
                    messages,
                    status_container,
                    max_tool_calls=35,
                    model=st.session_state.get("active_model", AZURE_MODEL_5),
                    top_results=st.session_state.get("top_results", 1)
                )
                response_placeholder.markdown(answer)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            except Exception as e:
                error_msg = "❌ Something went wrong. Please try again or contact support."
                response_placeholder.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

            finally:
                # Always unlock input when done
                st.session_state.is_processing = False

    # Sidebar
    with st.sidebar:
        st.header("🤖 Model")
        MODEL_OPTIONS = {
            "GPT-4.1": AZURE_MODEL_4,
            "GPT-5": AZURE_MODEL_5

        }
        selected_label = st.selectbox("Select model", list(MODEL_OPTIONS.keys()))
        selected_model = MODEL_OPTIONS[selected_label]

        if "active_model" not in st.session_state:
            st.session_state.active_model = selected_model

        if st.session_state.active_model != selected_model:
            st.session_state.active_model = selected_model
            st.session_state.messages = []
            st.session_state.is_processing = False
            st.rerun()

        st.divider()

        st.header("🔍 Search Settings")

        # Initialize top_results in session state if not present
        if "top_results" not in st.session_state:
            st.session_state.top_results = 1

        # Slider for top results
        top_results = st.slider(
            "Number of search results per query",
            min_value=1,
            max_value=3,
            value=st.session_state.top_results,
            step=1,
            help="⚖️ Increasing this value adds more context to the model but increases response time"
        )

        # Update session state if value changed
        if top_results != st.session_state.top_results:
            st.session_state.top_results = top_results

        st.header("💬 Chat Controls")

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.is_processing = False
            st.rerun()

        st.divider()

        st.header("ℹ️ Info")
        st.info(f"""
        **Model:** {st.session_state.get("active_model", "—")}
        **Messages:** {len(st.session_state.messages)}
        **Search Results:** {st.session_state.get("top_results", 1)} per query
        """)

        st.divider()

        with st.expander("🔧 Debug"):
            st.json({
                "total_messages": len(st.session_state.messages),
                "is_processing": st.session_state.is_processing,
                "session_id": id(st.session_state)
            })


if __name__ == "__main__":
    main()