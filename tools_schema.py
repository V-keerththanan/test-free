TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_testportfolio",
            "description": """Search the test portfolio index for parameter testing information.

MASTER TABLE - Call AFTER search_similar_parameters validates the parameter name.
Returns Test Code + Matrix Code needed for lookup tools.

USE WHEN:
- Parameter name has been validated by search_similar_parameters
- User asks about detection limits, reporting limits, test codes, methods
- User references a test code directly (e.g., F2648, F2202)

RETURNS:
Test code, test name, parameter name, matrix code/name, LOD, LOQ, reporting limit, units, methods.

QUERY TIPS:
- Include parameter name and matrix: "propylene glycol groundwater"
- Test codes work directly: "F2202", "F2648"
- Detection limits are in LOQ column (not LOD)

IMPORTANT:
- Test Code returned here links to logistics and turnaround tools
- Matrix Case contains regulation details — match against user's description""",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "string",
                        "description": """Search terms combining parameter name, matrix, and/or test code.
Example: "propylene glycol groundwater", "iron soil", "F2648", "PFAS AS3000\"
CRITICAL:
- This field must represent ONE logical analysis only.
- NEVER include multiple test codes, parameters, or matrices in a single string.
- If the user provides multiple analyses, call this tool separately for each.
- Do NOT merge multiple analyses into one search_query."""
                    }
                },
                "required": ["search_query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_sample_logistic",
            "description": """Search the sample logistics index for container, quantity, and preservation requirements.

PREREQUISITE (MANDATORY):
You MUST call search_testportfolio FIRST to get the Test Code before calling this tool.
This tool uses CI Code (= Test Code from Table 1) to find the correct row.
DO NOT call this tool with only a parameter name — first get the Test Code from search_testportfolio.

USE WHEN:
- User asks which container or bottle type is needed for a specific test
- User asks how much sample to provide (optimal or minimum quantity)
- User asks how long a sample can be stored before analysis (preservation time)
- User asks about sample density requirements
- User asks "Which bottle do I need for [test/parameter]?"
- User asks "How much soil/water do I need to send for [analysis]?"
- User asks "How long can I keep the sample before submitting?"
- User asks about the number of containers required for a test
- User provides a list of analyses and asks which containers are needed

RETURNS:
CI code (= test code), CI name,AMT code, AMT name, matrix code and name, preferred container code,
preferred container name, optimal sample amount, minimal sample amount,
sample amount unit, maximum preservation time in hours, approximate sample density,
optimal and minimal number of containers required.

SEARCH STRATEGY (PRIORITY ORDER):
1. FIRST: Search with Test Code ONLY (e.g., "F2202", "FF1Q2")
   - This gives exact CI Code match since CI Code = Test Code
   - Review results for Matrix Case match

2. IF NO CI CODE MATCH: Then search with Test Name or parameter name
   - Use CI Name which corresponds to Test Name

3. MATRIX SELECTION FROM RESULTS:
   - After search, review the Matrix Case field in results
   - Select the row matching user's matrix (e.g., "Ground water: regulation is RvA")
   - If no matrix match, fall back to "N/A" or "Default Case" rows

QUERY TIPS:
- Preservation time is always in HOURS (e.g., 672 hours = 28 days)
- When user provides multiple analyses, call this tool once per test code
- CI Code in this table = Test Code from Table 1
- CI Name in this table = Test Name from Table 1

IMPORTANT:
- Container code returned here (Preferred Type of Sample Container code)
  can be used to identify the physical bottle (e.g., 062, 064, 069, 080)
- These container codes are the same bottle numbers users reference in questions
- Sample quantity unit varies per test — always check the unit field (g, ml, l, kg)""",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "string",
                        "description": """PRIORITY: Search with Test Code ONLY first (e.g., "F2202", "FF1Q2").
If no CI Code match, then try Test Name (e.g., "VOCl", "Sulfate").

CRITICAL:
- First attempt: Use Test Code from search_testportfolio (highest priority)
- Second attempt: Use Test Name if Test Code search fails
- Matrix filtering: Review results and select matching Matrix Case
- One search query = one test code or test name only
- Do NOT combine multiple items in one search query."""
                    }
                },
                "required": ["search_query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_turnaround_times",
            "description": """Search the turnaround time index for standard and rush test completion times.

PREREQUISITE (MANDATORY):
You MUST call search_testportfolio FIRST to get the Test Code before calling this tool.
This tool uses Test Code (from Table 1) to find the correct row.
DO NOT call this tool with only a parameter name — first get the Test Code from search_testportfolio.

USE WHEN:
- User asks how long a test takes or when results will be ready
- User asks about turnaround time (TAT) for a specific test or parameter
- User asks about rush or expedited testing options
- User asks "Can you do this test faster?" or "Is there a rush option?"
- User asks about standard vs rush processing times
- User asks about minimum technical time required for a test
- User asks about accreditation or recognition status of a test
- User asks which lab or performer handles a specific test

RETURNS:
Test code, test name, matrix code and name, performer code and name,
standard TAT in days (interco_list_tat_d), standard TAT in hours (interco_list_tat_h),
TAT configuration preference (Days or Hours), rush TAT in days (interco_rush_level_4_tat_d),
rush TAT in hours (interco_rush_level_4_tat_h), rush TAT configuration preference,
minimum technical required time,recognition code, recognition name, recognition short code, accreditation details,
additional search words, internal and external translated test names.

SEARCH STRATEGY (PRIORITY ORDER):
1. FIRST: Search with Test Code ONLY (e.g., "F2202", "FF1Q2")
   - This gives exact Test Code match
   - Review results for Matrix Case match

2. IF NO MATCH: Then search with Test Name
   - Use Test Name which corresponds to Test Name from Table 1

3. MATRIX SELECTION FROM RESULTS:
   - After search, review the Matrix Case field in results
   - Select the row matching user's matrix
   - If no matrix match, fall back to "N/A" or "Default Case" rows

QUERY TIPS:
- Always check the TAT configuration preference field first:
  if preference = "Days" → read the _d field value
  if preference = "Hours" → read the _h field value
- NULL rush TAT values mean rush option is not available for that test and matrix
- Different matrices of the same test may have different turnaround times

IMPORTANT:
- Minimum technical required time is the absolute fastest possible —
  this is different from the standard or rush TAT
- Recognition name contains accreditation standard details
  (e.g., "NEN EN ISO/IEC 17025: 2017, RvA L010") — useful if user asks about accreditation
- Additional search words field catches informal or alternative parameter names
  that users may use in their question""",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "string",
                        "description": """PRIORITY: Search with Test Code ONLY first (e.g., "F2202", "FF1Q2").
If no match, then try Test Name (e.g., "VOCl", "Sulfate").

CRITICAL:
- First attempt: Use Test Code from search_testportfolio (highest priority)
- Second attempt: Use Test Name if Test Code search fails
- Matrix filtering: Review results and select matching Matrix Case
- One search query = one test code or test name only
- Do NOT combine multiple items in one search query."""
                    }
                },
                "required": ["search_query"]
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "search_containers",
        "description": """Search the container database for detailed container specifications, ordering configuration, and logistics information.

CRITICAL — ORDERING CONFIGURATION LAYER ONLY:
This tool provides ORDERING and LOGISTICS information about containers.
It tells you how containers can be ordered, packaged, purchased, and distributed.
It does NOT define which container a TEST or PARAMETER requires for analysis.
NEVER use this tool to determine analytical container requirements.
For analytical requirements, always use search_sample_logistic FIRST.

USE WHEN:
- User asks about barcode prefixes for a specific container (e.g., "What's the barcode for 062?")
- User asks about ordering quantities or box quantities (e.g., "How many containers in a box?")
- User asks if a container can be ordered individually (e.g., "Can I order CS012 individually?")
- User asks about purchasing codes or online ordering limits
- User references a TSC code or container code directly without mentioning a test
- User needs detailed container specifications beyond just the container name
- User asks operational or procurement questions about containers

DO NOT USE WHEN:
- User asks which container a TEST needs (use search_sample_logistic instead)
- User asks about sample amounts or preservation for a test (use search_sample_logistic instead)
- User asks which tests can share a container (use search_sample_logistic instead)

RETURNS:
TSC code, TSC name (full container description), TSC status (InUse/retired), 
TSC type (With Characteristics/Generic), TSC main barcode prefix, 
additional barcode prefixes, number of containers per box, 
maximum number allowed for online ordering, whether containers can be ordered individually, 
purchasing group item codes, commercial item usage status.

QUERY TIPS:
- Include TSC code if known: "CS012", "T0004", "COMPA"
- Include container code reference: "062", "064", "069", "080"
- Include container description: "brown glass bottle", "plastic jar", "green glass"
- Barcode prefixes are often the same as container codes (e.g., barcode 062 = container 062)

CONNECTION WITH OTHER TOOLS:
This tool connects to search_sample_logistic via the container code/TSC code field.

**SEQUENTIAL WORKFLOW FOR DUAL QUESTIONS:**
When user asks BOTH analytical requirement AND ordering info 
(e.g., "What container do I need for PFAS and can I order it individually?"):

Step 1 → Call search_sample_logistic("PFAS") first to get the required container code
Step 2 → Use that container code to call search_containers for ordering details
Step 3 → Present results in TWO separate sections:
  - Analytical Requirement: test code, required container, sample amount, preservation
  - Ordering Configuration: TSC code, barcode, ordering limits, box quantities

**DIRECT USE FOR ORDERING-ONLY QUESTIONS:**
When user asks ONLY about ordering (e.g., "Can I order container 062 individually?"):
Call search_containers("062") directly without calling search_sample_logistic first.

**FALLBACK RULE:**
If search_sample_logistic returns no result for a test:
- You may check search_containers for container definition only
- But clearly state: "Analytical requirement could not be confirmed from our database"
- Never guess which container a test requires based on ordering data

IMPORTANT:
- TSC code in this tool = Preferred Type of Sample Container code in search_sample_logistic
- Container codes (062, 064, 069, 080) and TSC codes (CS012, T0004) may refer to the same physical container
- Barcode prefixes are used for sample tracking and identification in the lab
- "InUse" status means the container is currently active and available
- "Generic" TSC type means the container definition is not tied to specific characteristics
- Always maintain strict separation between analytical requirements (what the test needs)
  and ordering configuration (how to procure the container)

CUSTOMER COMMUNICATION:
- tsc_main_barcode_prefix is the customer-facing bottle identifier (e.g., 067, 069, 080)
- ALWAYS use this barcode prefix when communicating with customers, NOT internal TSC codes
- Customers recognize bottles by their barcode prefix numbers
- Example response format: "For VOCl: use bottle 067" or "Sulfate requires container 062\"""",
        "parameters": {
            "type": "object",
            "properties": {
                "search_query": {
                    "type": "string",
                    "description": """Search terms for TSC code, container code, barcode prefix, or container description.
Example: "CS012", "brown glass bottle 250ml", "container 062 barcode", "T0004 ordering"

CRITICAL TOOL CALL RULE:
- The search_query must correspond to ONE container only.
- NEVER combine multiple TSC codes, container codes, or barcode prefixes in one string.
- If the user asks about multiple containers, you MUST call this tool separately for each one.
- Do NOT merge multiple container queries into a single search_query."""
                }
            },
            "required": ["search_query"]
        }
    }
}
,
    {
        "type": "function",
        "function": {
            "name": "find_cas_number",
            "description": """Find the CAS Registry Number for a chemical parameter name.

USE WHEN:
- The parameter name in the search results does NOT exactly match what the user asked for
- Search returns a similar but different parameter (e.g., user asked "propylene glycol" but results show "ethylene glycol")
- Parameter name search returns no results
- You need to identify the exact chemical substance before searching again

CRITICAL MATCHING RULE:
After calling search_testportfolio, ALWAYS compare the returned ParameterName with what the user asked.
If they are NOT the same substance, you MUST call find_cas_number to get the CAS number and search again.

Example:
- User asks: "propylene glycol" → Results show: "ethylene glycol" → NOT A MATCH → Call find_cas_number

RETURNS:
- parameter_name: The input parameter name
- cas_number: The CAS Registry Number (e.g., "57-55-6") or "UNKNOWN"
- status: "found", "not_found", or "error"

WORKFLOW:
1. Search test_portfolio with the parameter name
2. Compare returned ParameterName with user's requested parameter
3. If NOT a match → call find_cas_number to get CAS number
4. Search test_portfolio again using the CAS number
5. This ensures you return data for the EXACT parameter the user asked about

IMPORTANT:
- NEVER answer with data from a different parameter than what the user asked
- This tool uses AI to look up CAS numbers - results should be verified
- If status is "not_found" or "error", inform the user the parameter could not be identified
- Common CAS examples: Propylene glycol = 57-55-6, Vinyl Chloride = 75-01-4""",
            "parameters": {
                "type": "object",
                "properties": {
                    "parameter_name": {
                        "type": "string",
                        "description": "The chemical parameter name to look up (e.g., 'propylene glycol', 'vinyl chloride', 'benzene')"
                    }
                },
                "required": ["parameter_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_database_schema",
            "description": """Get comprehensive schema information and sample data from ALL 4 databases in one call.

RETURNS COMPLETE DATABASE STRUCTURE:
- Table 1: Test Portfolio (tests, parameters, limits, methods, accreditation)
- Table 2: Sample Logistics (containers, quantities, preservation times)
- Table 3: Turnaround Times (standard TAT, rush TAT, performer info)
- Table 4: Containers (container specs, barcodes, ordering info)

EACH TABLE INCLUDES:
- Field definitions (what each column means)
- Business logic and linking rules
- 1 real sample record showing actual data format
- Important notes about data interpretation

TABLE RELATIONSHIPS:
- Test Code (Table 1) = CI Code (Table 2) = Test Code (Table 3)
- Preferred Type of Sample Container code (Table 2) = TSC code (Table 4)
- Matrix Code links Table 1, 2, and 3

BENEFITS:
- See complete database structure and how tables connect
- Understand parameter naming patterns across all tables
- Learn test code formats and container code relationships
- Identify exact field names for crafting precise search queries
- Understand matrix naming and N/A fallback logic

WHEN TO USE:
- At the start of a conversation to understand available data
- When unfamiliar with parameter/test names
- When previous searches returned no results
- When needing to decompose complex multi-parameter queries

This is a ZERO-PARAMETER tool - just call it to get all schemas at once.""",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    # =============================
    # KEYWORD/FILTER LOOKUP TOOLS
    # (For exact code matching - no semantic ambiguity)
    # =============================
    {
        "type": "function",
        "function": {
            "name": "lookup_logistics_by_testcode",
            "description": """Lookup sample logistics (containers, quantities, preservation) by exact Test Code.

WHEN TO USE:
- You already have the Test Code from search_testportfolio
- You need container, sample quantity, or preservation time for a specific test
- You want GUARANTEED exact match on test code (no semantic ambiguity)

WHY USE THIS INSTEAD OF search_sample_logistic:
- search_sample_logistic uses semantic search which can return WRONG results
- Example: searching "FF1Q2 groundwater" may return ci_code="PF185" (wrong!)
- This tool uses keyword search on ci_code field ONLY = exact match guaranteed

PREREQUISITE:
You MUST have the Test Code first from calling search_testportfolio.
The CI Code in this table equals the Test Code from Table 1.

RETURNS:
All matrix variations for the given test code, including:
- CI code and name
- Matrix case and code
- Preferred container code and name
- Optimal and minimal sample amounts with units
- Maximum preservation time in hours
- Number of containers required

WORKFLOW:
1. Call search_testportfolio to get Test Code (e.g., "F2202")
2. Call lookup_logistics_by_testcode("F2202")
3. Select the row matching user's matrix from results
4. Use container code to call lookup_container_by_code for barcode prefix

IMPORTANT:
- This function returns ALL matrix variations for the test code
- YOU must select the correct matrix row based on user's context
- If no exact matrix match, use "N/A" or "Default Case" rows""",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_code": {
                        "type": "string",
                        "description": "The exact Test Code to lookup (e.g., 'F2202', 'FF1Q2', 'PF185'). Do NOT include matrix text."
                    }
                },
                "required": ["test_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_tat_by_testcode",
            "description": """Lookup turnaround times by exact Test Code.

WHEN TO USE:
- You already have the Test Code from search_testportfolio
- You need standard TAT, rush TAT, or performer info for a specific test
- You want GUARANTEED exact match on test code (no semantic ambiguity)

WHY USE THIS INSTEAD OF search_turnaround_times:
- search_turnaround_times uses semantic search which can return WRONG results
- This tool uses keyword search on test_code field ONLY = exact match guaranteed

PREREQUISITE:
You MUST have the Test Code first from calling search_testportfolio.

RETURNS:
All matrix variations for the given test code, including:
- Test code and name
- Matrix case and code
- Standard TAT (days/hours) with configuration preference
- Rush TAT (days/hours) - NULL if not available
- Minimum technical required time
- Performer name and code
- Recognition/accreditation details

TAT READING RULE:
Check "IntercoListTATConfigurationPreference" field first:
- If "Days" → read IntercoListTAT_D
- If "Hours" → read IntercoListTAT_H

WORKFLOW:
1. Call search_testportfolio to get Test Code
2. Call lookup_tat_by_testcode with the Test Code
3. Select the row matching user's matrix from results""",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_code": {
                        "type": "string",
                        "description": "The exact Test Code to lookup (e.g., 'F2202', 'FF1Q2'). Do NOT include matrix text."
                    }
                },
                "required": ["test_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_container_by_code",
            "description": """Lookup container specifications by exact TSC code or barcode prefix.

WHEN TO USE:
- You have a container code from lookup_logistics_by_testcode (Preferred Type of Sample Container code)
- You need the barcode prefix for customer communication
- You need ordering information (box quantities, individual ordering)

PREREQUISITE:
Call lookup_logistics_by_testcode first to get the container code.
The TSC code here matches the "Preferred Type of Sample Container code" from Table 2.

RETURNS:
- TSC code and name
- TSC main barcode prefix (USE THIS for customer communication!)
- Status (In Use / Retired)
- Number of containers per box
- Maximum number for online ordering
- Whether containers can be ordered individually

CUSTOMER COMMUNICATION:
ALWAYS use tsc_main_barcode_prefix (e.g., "067", "080") when talking to customers.
NEVER use internal TSC codes (CS012, T0004) in customer responses.

WORKFLOW:
1. lookup_logistics_by_testcode returns container code (e.g., "ORPA")
2. Call lookup_container_by_code("ORPA")
3. Get barcode prefix (e.g., "067")
4. Tell customer: "Use bottle 067" """,
            "parameters": {
                "type": "object",
                "properties": {
                    "container_code": {
                        "type": "string",
                        "description": "The TSC code or barcode prefix to lookup (e.g., 'ORPA', '067', 'CS012')"
                    }
                },
                "required": ["container_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_testportfolio_by_code",
            "description": """Lookup test portfolio by exact Test Code or CAS number.

WHEN TO USE:
- You have an exact Test Code and need all parameter details for that test
- You have a CAS number and need to find the exact matching parameter
- Semantic search returned wrong results and you need exact matching
- User provided a CAS number directly in their question

WHY USE THIS:
- search_testportfolio uses semantic search which may return WRONG parameter
- Example: searching "75-01-4 groundwater" may return 4-Ethyltoluene (CAS 622-96-8) instead of Vinyl Chloride
- This tool uses keyword search = exact CAS or test code match guaranteed

RETURNS:
All rows matching the code, including:
- Test code and name
- Parameter name and code
- Matrix case and code
- LOQ, LOD, Reporting Limit with units
- Method and accreditation details

CAS NUMBER LOOKUP:
Use this when:
1. User provided a CAS number directly
2. find_cas_number tool returned a CAS number
3. Semantic search returned wrong parameter (use CAS for retry)

Example: lookup_testportfolio_by_code("75-01-4", "cas_number")
→ Returns Vinyl Chloride data exactly""",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The code to search for (Test Code like 'F2202' or CAS number like '75-01-4')"
                    },
                    "code_type": {
                        "type": "string",
                        "enum": ["test_code", "cas_number"],
                        "description": "Type of code: 'test_code' for test codes, 'cas_number' for CAS registry numbers"
                    }
                },
                "required": ["code", "code_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_similar_parameters",
            "description": """FIRST TOOL TO CALL when user asks about a parameter or test by name.
Searches for exact or similar parameter/test names with their available matrices and test codes.

CALL THIS FIRST BEFORE search_testportfolio when user provides a parameter/test name.

WORKFLOW:
1. User mentions a parameter/test name → call this tool first
2. Check results:
   - EXACT MATCH found → proceed with search_testportfolio or get_container_requirements_for_tests
   - SIMILAR matches found → ask user to clarify which one they meant
   - NO match → inform user parameter not found, ask for clarification
3. After user confirms → use confirmed name with search_testportfolio

RETURNS (Hierarchical Structure):
- matches: List of matches, each containing:
  - parameter_name: The parameter name
  - test_name: The test name
  - test_codes: List of test code objects, each containing:
    - test_code: The test code (e.g., "F1847")
    - matrices: List of matrices available for this specific test_code
- count: Number of matches
- status: success/error
- next_step: Instructions for what to do next

EXAMPLE RESPONSE:
{
  "matches": [{
    "parameter_name": "Calcium",
    "test_name": "Calcium (Ca)",
    "test_codes": [
      {"test_code": "F1847", "matrices": ["Soil...", "Materials..."]},
      {"test_code": "FF1S6", "matrices": ["WATER...", "Mineral..."]}
    ]
  }]
}

TO GET TEST CODE FOR USER'S MATRIX:
1. Find matching parameter_name + test_name
2. Look through test_codes array
3. Find test_code where matrices contains user's matrix
4. Use that test_code for get_container_requirements_for_tests or lookup tools""",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "Parameter name or test name from user input"
                    }
                },
                "required": ["search_term"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_container_requirements_for_tests",
            "description": """Analyze container requirements for multiple tests and identify bottle sharing opportunities.

USE WHEN:
- User asks "How many bottles do I need for tests X, Y, Z?"
- User asks "Can these tests share a container?"
- User wants to optimize sample submission
- User asks about container requirements for multiple parameters

PREREQUISITE:
Get test codes first using search_similar_parameters (returns test_codes[]).

SHARING LOGIC (evaluated by LLM):
- Tests with same AMT code (Analytical Method Template) → can potentially share
- Within same AMT group, tests must have same container name → can share
- Sharing rule must be "Shareable if same AMT" → can share
- Combined MRV (Minimum Required Volume) must fit in container capacity
- Different AMT codes = separate containers required
- "Not shareable" or "N/A" sharing rule = separate containers

WORKFLOW:
1. Call search_similar_parameters for each parameter → get test_codes
2. Collect all test_codes into a list
3. Call get_container_requirements_for_tests(test_codes, matrix)
4. Explain results to user (bottles needed, sharing opportunities)

RETURNS:
- total_bottles_needed: Number of bottles required with sharing
- bottles_without_sharing: Number if each test had its own bottle
- bottles_saved: Difference showing optimization benefit
- container_groups: Detailed breakdown by container/AMT group
  - Each group shows: tests that can share, container name, capacity, total MRV, reason
- tests_not_found: Any test codes that couldn't be looked up

EXAMPLE:
User: "How many bottles for iron, manganese, sodium in groundwater?"
1. search_similar_parameters("iron") → test_codes: ["F1068"]
2. search_similar_parameters("manganese") → test_codes: ["F1070"]
3. search_similar_parameters("sodium") → test_codes: ["F1073"]
4. get_container_requirements_for_tests(["F1068", "F1070", "F1073"], "groundwater")
5. Result: 1 bottle needed (all share same AMT, same container, shareable rule)""",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_codes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of test codes to analyze (get from search_similar_parameters)"
                    },
                    "matrix": {
                        "type": "string",
                        "description": "Optional matrix filter (e.g., 'groundwater', 'soil'). Filters logistics data to matching matrix."
                    }
                },
                "required": ["test_codes"]
            }
        }
    }
]