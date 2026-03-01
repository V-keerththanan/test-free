import logging
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load from .env for local development
load_dotenv("azure.env")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def get_secret(key: str) -> str:
    """Get secret from Streamlit Cloud secrets or environment variables."""
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except ImportError:
        pass
    return os.getenv(key)

# --- Azure Search Configuration (loaded from secrets or env) ---
SEARCH_ENDPOINT = get_secret("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = get_secret("AZURE_SEARCH_KEY")
INDEX_NAME = get_secret("AZURE_SEARCH_INDEX_1")
INDEX_NAME_2 = get_secret("AZURE_SEARCH_INDEX_2")
INDEX_NAME_3 = get_secret("AZURE_SEARCH_INDEX_3")
INDEX_NAME_4 = get_secret("AZURE_SEARCH_INDEX_4")

def search_testportfolio(search_query: str, top: int = 1):
    client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    try:
        results = client.search(
            search_text=search_query,
            query_type="semantic",
            semantic_configuration_name="azuresql-test-portfolio-sc",
            top=top
        )
        return [result for result in results]
    except Exception as e:
        logger.error(e)
        return "Not able to fetch the data at the moment"


def search_sample_logistic(search_query: str, top: int = 1):
    client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME_2,
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    try:
        results = client.search(
            search_text=search_query,
            query_type="semantic",
            semantic_configuration_name="azuresql-index-sampling-logistics",
            top=top
        )
        return [result for result in results]
    except Exception as e:
        logger.error(e)
        return "Not able to fetch the data at the moment"


def search_turnaround_times(search_query: str, top: int = 1):
    client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME_3,
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    try:
        results = client.search(
            search_text=search_query,
            query_type="semantic",
            semantic_configuration_name="azuresql-index-turn-around",
            top=top
        )
        return [result for result in results]
    except Exception as e:
        logger.error(e)
        return "Not able to fetch the data at the moment"


def search_containers(search_query: str, top: int = 1):
    """Search the container/TSC index for container details."""
    client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME_4,
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    try:
        results = client.search(
            search_text=search_query,
            query_type="semantic",
            semantic_configuration_name="azuresql-index-container",
            top=top
        )
        return [result for result in results]
    except Exception as e:
        logger.error(e)

        return "Not able to fetch the data at the moment"


# =============================
# SCHEMA RETRIEVAL FUNCTIONS
# =============================

def get_database_schema():
    """Get comprehensive schema and sample data from ALL 4 databases to understand complete data structure and table relationships.

    This function returns schema information for:
    - Table 1: Test Portfolio (tests, parameters, limits, methods)
    - Table 2: Sample Logistics (containers, sample quantities, preservation)
    - Table 3: Turnaround Times (standard TAT, rush TAT, performer info)
    - Table 4: Containers (container specs, barcodes, ordering info)

    Each table includes field descriptions, linking logic, and 1 sample record.
    """

    all_schemas = {
        "overview": "Complete database structure with 4 interconnected tables",
        "table_relationships": {
            "Table_1_to_Table_2": "Test Code (Table 1) = CI Code (Table 2)",
            "Table_1_to_Table_3": "Test Code + Matrix Code link both tables",
            "Table_2_to_Table_4": "Preferred Type of Sample Container code (Table 2) = TSC code (Table 4)",
            "workflow": "Start with Table 1 (test/parameter) → use Test Code to get logistics (Table 2), TAT (Table 3), and container details (Table 4)"
        },
        "tables": {}
    }

    # Table 1: Test Portfolio
    try:
        client = SearchClient(
            endpoint=SEARCH_ENDPOINT,
            index_name=INDEX_NAME,
            credential=AzureKeyCredential(SEARCH_KEY)
        )
        results = client.search(search_text="*", top=1)
        samples = [dict(result) for result in results]

        all_schemas["tables"]["table_1_test_portfolio"] = {
            "description": "PRIMARY TABLE - Contains test parameters, detection limits, methods, units, and accreditation. Use Test Code + Parameter Code + Matrix Code to uniquely identify a row.",
            "key_fields": {
                "TestCode": "Unique test identifier (e.g., F-12345, F2202). CRITICAL for linking to Tables 2, 3, and 4.",
                "TestName": "Full name of the test",
                "ParameterName": "Name of substance/parameter being tested (e.g., 'Propylene glycol', 'Strontium')",
                "ParameterCode": "Unique parameter identifier code",
                "MatrixCase": "Sample type with regulation context (e.g., 'Ground water: regulation is RvA'). IMPORTANT: If no exact match found, ALWAYS fall back to 'N/A' or 'Default Case' matrices.",
                "MatrixCode": "Matrix identifier code",
                "LOD": "Limit of Detection value. NOTE: Often NULL - use LOQ or ReportingLimit instead.",
                "LOQ": "Limit of Quantification value",
                "ReportingLimit": "Reporting Limit value",
                "LimitUnitNumerator": "Unit numerator for limits (e.g., 'µg', 'mg')",
                "LimitUnitDenominator": "Unit denominator for limits (e.g., 'L', 'kg')",
                "Method": "Analysis method used",
                "AccreditationStatus": "Accreditation and recognition details"
            },
            "important_notes": [
                "A row is uniquely identified by: Test Code + Parameter Code + Matrix Code",
                "When matrix is unknown or not found, ALWAYS fall back to 'N/A' or 'Default Case'",
                "LOD is often NULL - use LOQ or Reporting Limit instead",
                "For 'Which test do I need?' questions: search by Parameter Name (+ Matrix if known)",
                "Same parameter can have multiple test codes for different matrices",
                "Units are always: Limit Unit Numerator / Limit Unit Denominator"
            ],
            "sample_record": samples[0] if samples else None
        }
    except Exception as e:
        logger.error(f"Error fetching test portfolio schema: {e}")
        all_schemas["tables"]["table_1_test_portfolio"] = {"error": "Unable to fetch schema"}

    # Table 2: Sample Logistics
    try:
        client = SearchClient(
            endpoint=SEARCH_ENDPOINT,
            index_name=INDEX_NAME_2,
            credential=AzureKeyCredential(SEARCH_KEY)
        )
        results = client.search(search_text="*", top=1)
        samples = [dict(result) for result in results]

        all_schemas["tables"]["table_2_sample_logistics"] = {
            "description": "Contains container requirements, sample quantities, preservation, and density. Links to Table 1 via CI code (= Test Code) + Matrix Code. Links to Table 4 via 'Preferred Type of Sample Container code'.",
            "key_fields": {
                "CICode": "Commercial Item code - SAME AS Test Code from Table 1. Use this to link tables.",
                "CIName": "Commercial Item name - corresponds to Test Name",
                "MatrixCase": "Sample matrix type. REMEMBER: 'N/A' and 'Default Case' are fallback values.",
                "MatrixCode": "Matrix identifier code for linking",
                "PreferredTypeOfSampleContainerCode": "Container code (e.g., 062, 064, 069, 080). CRITICAL: Use this to link to Table 4 (TSC code).",
                "PreferredTypeOfSampleContainerName": "Container name/description",
                "OptimalAmountOfSample": "Optimal sample quantity (ALWAYS combine with Sample amount Unit)",
                "MinimalAmountOfSample": "Minimum sample quantity (ALWAYS combine with Sample amount Unit)",
                "SampleAmountUnit": "Unit for quantities (g, ml, l, kg)",
                "MaximumSamplePreservationTime": "Preservation time in HOURS (e.g., 672 hours = 28 days)",
                "ApproximateSampleDensity": "Sample density information",
                "OptimalNumberOfContainersRequired": "Optimal number of containers",
                "MinimalNumberOfContainersRequired": "Minimum number of containers"
            },
            "important_notes": [
                "CI Code in this table = Test Code in Table 1",
                "Link to Table 1: CI Code + Matrix Code",
                "Link to Table 4: Preferred Type of Sample Container code = TSC code",
                "Preservation time is ALWAYS in hours (convert to days: hours/24)",
                "Sample quantities MUST be reported with their unit",
                "When asked 'which container?', use Preferred Type of Sample Container fields",
                "N/A and Default Case are fallback matrix values"
            ],
            "sample_record": samples[0] if samples else None
        }
    except Exception as e:
        logger.error(f"Error fetching sample logistics schema: {e}")
        all_schemas["tables"]["table_2_sample_logistics"] = {"error": "Unable to fetch schema"}

    # Table 3: Turnaround Times
    try:
        client = SearchClient(
            endpoint=SEARCH_ENDPOINT,
            index_name=INDEX_NAME_3,
            credential=AzureKeyCredential(SEARCH_KEY)
        )
        results = client.search(search_text="*", top=1)
        samples = [dict(result) for result in results]

        all_schemas["tables"]["table_3_turnaround_times"] = {
            "description": "Contains standard TAT, rush TAT, minimum technical time, performer info, and accreditation. Links to Table 1 via Test Code + Matrix Code.",
            "key_fields": {
                "TestCode": "Test identifier - SAME AS Test Code in Table 1. Use this to link tables.",
                "TestName": "Full test name",
                "MatrixCase": "Sample matrix type. REMEMBER: 'N/A' and 'Default Case' are fallback values.",
                "MatrixCode": "Matrix identifier code",
                "IntercoListTAT_D": "Standard turnaround time in DAYS",
                "IntercoListTAT_H": "Standard turnaround time in HOURS",
                "IntercoListTATConfigurationPreference": "Which TAT field to use: 'Days' or 'Hours'. CHECK THIS FIRST!",
                "IntercoRushLevel4TAT_D": "Rush turnaround time in DAYS (NULL = no rush option)",
                "IntercoRushLevel4TAT_H": "Rush turnaround time in HOURS (NULL = no rush option)",
                "IntercoRushTATConfigurationPreference": "Which rush TAT field to use: 'Days' or 'Hours'",
                "MinimumTechnicalRequiredTime": "Absolute fastest possible time (different from standard/rush)",
                "Performer": "Lab/performer name and location",
                "PerformerCode": "Performer identifier",
                "RecognitionName": "Accreditation standard details (e.g., 'NEN EN ISO/IEC 17025: 2017, RvA L010')",
                "RecognitionCode": "Recognition/accreditation code"
            },
            "important_notes": [
                "Link to Table 1: Test Code + Matrix Code",
                "ALWAYS check TAT Configuration Preference FIRST to know which field to read (Days or Hours)",
                "If Interco List TAT Configuration Preference = 'Days', read IntercoListTAT_D",
                "If Interco List TAT Configuration Preference = 'Hours', read IntercoListTAT_H",
                "NULL rush TAT = no rush option available for that test/matrix",
                "Different matrices of same test may have different TAT",
                "Minimum Technical Required Time is the absolute fastest (not standard/rush)",
                "N/A and Default Case are fallback matrix values"
            ],
            "sample_record": samples[0] if samples else None
        }
    except Exception as e:
        logger.error(f"Error fetching turnaround schema: {e}")
        all_schemas["tables"]["table_3_turnaround_times"] = {"error": "Unable to fetch schema"}

    # Table 4: Containers
    try:
        client = SearchClient(
            endpoint=SEARCH_ENDPOINT,
            index_name=INDEX_NAME_4,
            credential=AzureKeyCredential(SEARCH_KEY)
        )
        results = client.search(search_text="*", top=1)
        samples = [dict(result) for result in results]

        all_schemas["tables"]["table_4_containers"] = {
            "description": "Contains container specifications, barcode prefixes, ordering quantities, and box quantities. Links to Table 2 via TSC code = 'Preferred Type of Sample Container code'.",
            "key_fields": {
                "TSCCode": "Type of Sample Container code. CRITICAL: This matches 'Preferred Type of Sample Container code' in Table 2.",
                "TSCName": "Full container description/name in English",
                "TSCStatus": "'In Use' (active/available) or 'Retired' (no longer available)",
                "TSCType": "'With Characteristics' (specific specs) or 'Generic' (standard container)",
                "TSCMainBarcodePrefix": "Primary barcode prefix for sample tracking (often same as container code, e.g., '062')",
                "TSCAdditionalBarcodePrefixes": "Additional barcode prefixes if applicable",
                "NumberOfContainersPerBox": "How many containers come in one box",
                "MaximumNumberAllowedForOnlineOrdering": "Maximum quantity for online orders",
                "ContainersCanBeOrderedIndividually": "Yes/No - whether single container orders are allowed",
                "PurchasingGroupItemCode": "Purchasing/procurement codes (TSC/CS codes)",
                "CommercialItemUsageStatus": "Usage status information"
            },
            "important_notes": [
                "Link to Table 2: TSC code = Preferred Type of Sample Container code",
                "Container codes (062, 064, 069, 080) often match TSC codes and barcode prefixes",
                "WORKFLOW: Table 1 (Test) → Table 2 (Container code) → Table 4 (TSC details)",
                "For 'which container for test X?': Start with Table 2, then use container code to query Table 4",
                "TSC Status 'In Use' means container is currently active and available",
                "Barcode prefixes are used for sample tracking and lab identification",
                "This table is ONLY for ordering/logistics - NOT for analytical requirements"
            ],
            "sample_record": samples[0] if samples else None
        }
    except Exception as e:
        print(e)
        logger.error(f"Error fetching containers schema: {e}")
        all_schemas["tables"]["table_4_containers"] = {"error": "Unable to fetch schema"}

    return all_schemas


# =============================
# KEYWORD/FILTER LOOKUP FUNCTIONS
# (For exact code matching - no semantic ambiguity)
# =============================

def lookup_logistics_by_testcode(test_code: str, top: int = 5):
    """
    Lookup sample logistics by exact Test Code (CI Code).
    Uses simple keyword search for exact matching instead of semantic search.
    Returns all matrix variations for the given test code.
    """
    client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME_2,
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    try:
        # Use simple query type for exact keyword matching
        # Search only the test code, no additional text
        results = client.search(
            search_text=test_code,
            query_type="simple",
            search_fields=["ci_code"],  # Restrict search to ci_code field only
            top=top
        )
        return [result for result in results]
    except Exception as e:
        logger.error(f"lookup_logistics_by_testcode error: {e}")
        return "Not able to fetch the data at the moment"


def lookup_tat_by_testcode(test_code: str, top: int = 5):
    """
    Lookup turnaround times by exact Test Code.
    Uses simple keyword search for exact matching instead of semantic search.
    Returns all matrix variations for the given test code.
    """
    client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME_3,
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    try:
        results = client.search(
            search_text=test_code,
            query_type="simple",
            search_fields=["test_code"],  # Restrict search to test_code field only
            top=top
        )
        return [result for result in results]
    except Exception as e:
        logger.error(f"lookup_tat_by_testcode error: {e}")
        return "Not able to fetch the data at the moment"


def lookup_container_by_code(container_code: str, top: int = 5):
    """
    Lookup container details by exact TSC code or barcode prefix.
    Uses simple keyword search for exact matching.
    """
    client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME_4,
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    try:
        results = client.search(
            search_text=container_code,
            query_type="simple",
            search_fields=["tsc_code", "tsc_main_barcode_prefix"],
            top=top
        )
        return [result for result in results]
    except Exception as e:
        logger.error(f"lookup_container_by_code error: {e}")
        return "Not able to fetch the data at the moment"


def lookup_testportfolio_by_code(code: str, code_type: str = "test_code", top: int = 5):
    """
    Lookup test portfolio by exact code (test_code or CAS number).
    Uses simple keyword search for exact matching.

    Args:
        code: The code to search for
        code_type: "test_code" or "cas_number"
    """
    client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    try:
        search_field = "test_code" if code_type == "test_code" else "cas_registry_number"
        results = client.search(
            search_text=code,
            query_type="simple",
            search_fields=[search_field],
            top=top
        )
        return [result for result in results]
    except Exception as e:
        logger.error(f"lookup_testportfolio_by_code error: {e}")
        return "Not able to fetch the data at the moment"


# =============================
# PARAMETER/TEST SEARCH FUNCTION
# =============================

def search_similar_parameters(search_term: str, top: int = 10) -> dict:
    """
    Search for parameters or tests similar to user input.
    Returns top matching parameter/test names with their available matrices and test codes.
    """
    client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_KEY)
    )

    try:
        results = client.search(
            search_text=search_term,
            query_type="semantic",
            semantic_configuration_name="azuresql-test-portfolio-sc",
            search_fields=["parameter_name", "test_name"],
            select=["parameter_name", "test_name", "test_code", "matrix_case_name_legacy_matrix_name"],
            top=top
        )

        # Group by parameter_name + test_name
        # Within each group, sub-group test_codes with their matrices
        matches = {}
        for result in results:
            param = result.get("parameter_name", "")
            test = result.get("test_name", "")
            matrix = result.get("matrix_case_name_legacy_matrix_name", "")
            test_code = result.get("test_code", "")

            key = f"{param}|{test}"
            if key not in matches:
                matches[key] = {
                    "parameter_name": param,
                    "test_name": test,
                    "test_codes": {}  # Dict: test_code -> list of matrices
                }

            if test_code:
                if test_code not in matches[key]["test_codes"]:
                    matches[key]["test_codes"][test_code] = []
                if matrix and matrix not in matches[key]["test_codes"][test_code]:
                    matches[key]["test_codes"][test_code].append(matrix)

        # Convert to final hierarchical format
        match_list = []
        for match in matches.values():
            match_list.append({
                "parameter_name": match["parameter_name"],
                "test_name": match["test_name"],
                "test_codes": [
                    {"test_code": tc, "matrices": matrices}
                    for tc, matrices in match["test_codes"].items()
                ]
            })

        return {
            "search_term": search_term,
            "matches": match_list,
            "count": len(match_list),
            "status": "success",
            "next_step": (
                "If exact match found with user's matrix → proceed with search_testportfolio or get_container_requirements_for_tests. "
                "If parameter not available with requested matrix → show available matrices and ask user which to proceed with. "
                "If no match → show similar options and ask user to confirm."
            )
        }

    except Exception as e:
        logger.error(f"search_similar_parameters error: {e}")
        return {
            "search_term": search_term,
            "matches": [],
            "count": 0,
            "status": "error",
            "error": str(e),
            "next_step": "Inform user of error and ask to rephrase query."
        }


# =============================
# CAS NUMBER LOOKUP FUNCTION
# =============================

def find_cas_number(parameter_name: str) -> dict:
    """
    Calls GPT to find the CAS Registry Number for a chemical parameter.
    Returns dict with cas_number and status.
    """
    client = AzureOpenAI(
        azure_endpoint=get_secret("AZURE_OPENAI_ENDPOINT_4"),
        api_key=get_secret("AZURE_OPENAI_API_KEY_4"),
        api_version=get_secret("AZURE_OPENAI_API_VERSION_4")
    )

    try:
        response = client.chat.completions.create(
            model=get_secret("AZURE_OPENAI_MODEL_4"),
            messages=[
                {
                    "role": "system",
                    "content": """You are a chemistry expert. When given a chemical substance name,
return ONLY its CAS Registry Number in the format XXX-XX-X or XXXXX-XX-X.
If you are not certain or the substance is not a single chemical compound,
return "UNKNOWN".
Do not include any explanation, just the CAS number or UNKNOWN."""
                },
                {
                    "role": "user",
                    "content": f"What is the CAS Registry Number for: {parameter_name}"
                }
            ],
            temperature=0,
            max_tokens=50
        )

        cas_number = response.choices[0].message.content.strip()

        return {
            "parameter_name": parameter_name,
            "cas_number": cas_number,
            "status": "found" if cas_number != "UNKNOWN" else "not_found"
        }

    except Exception as e:
        logger.error(f"CAS lookup error: {e}")
        return {
            "parameter_name": parameter_name,
            "cas_number": None,
            "status": "error",
            "error": str(e)
        }


# =============================
# BOTTLE REQUIREMENTS FUNCTION
# =============================

def get_container_requirements_for_tests(test_codes: list, matrix: str = None) -> dict:
    """
    Analyze container requirements for multiple tests using LLM.
    1. Fetches logistics data for each test code
    2. Sends data to GPT for analysis
    3. GPT determines sharing opportunities and bottle count
    """
    import json

    # 1. Fetch logistics for each test code
    test_data = []
    tests_not_found = []

    for test_code in test_codes:
        logistics = lookup_logistics_by_testcode(test_code, top=10)
        if logistics and not isinstance(logistics, str):
            for row in logistics:
                row_dict = dict(row) if hasattr(row, 'items') else row
                # Filter by matrix if provided
                if matrix:
                    matrix_value = str(row_dict.get("matrix_case_name_legacy_matrix_name", "")).lower()
                    if matrix.lower() in matrix_value:
                        test_data.append(row_dict)
                        break
                else:
                    test_data.append(row_dict)
                    break
        else:
            tests_not_found.append(test_code)

    if not test_data:
        return {
            "status": "error",
            "error": "No logistics data found for any test codes",
            "tests_not_found": tests_not_found
        }

    # 2. Prepare data summary for LLM
    data_for_llm = []
    for row in test_data:
        data_for_llm.append({
            "test_code": row.get("ci_code"),
            "test_name": row.get("ci_name"),
            "container_code": row.get("preferred_type_of_sample_container_code"),
            "container_name": row.get("preferred_type_of_sample_container_name"),
            "amt_code": row.get("amt_code"),
            "amt_name": row.get("amt_name"),
            "sharing_rule": row.get("sample_quantity_sharing_rule"),
            "minimal_sample": row.get("minimal_amount_of_sample"),
            "sample_unit": row.get("sample_amount_unit"),
            "matrix": row.get("matrix_case_name_legacy_matrix_name")
        })

    # 3. Call LLM to analyze using detailed workflow
    prompt = f"""Analyze these test logistics and determine bottle sharing opportunities.

TEST DATA:
{json.dumps(data_for_llm, indent=2)}

FOLLOW THESE STEPS EXACTLY:

STEP 1 — GROUP BY AMT CODE
- Group all parameters by amt_code
- Only parameters with SAME AMT can potentially share containers

STEP 2 — EVALUATE EACH AMT GROUP
Case A: Group has only 1 parameter → Separate bottle required (no sharing possible)
Case B: Group has 2+ parameters → Continue to container evaluation

STEP 3 — CHECK CONTAINER NAME MATCH
Within each AMT group:
- Compare "container_name" for all tests
- If container names are DIFFERENT → Cannot share, split into subgroups by container
- If container names are IDENTICAL → Sharing is technically possible, continue

STEP 4 — EVALUATE SHARING RULE
Check "sharing_rule" field (only these values exist in data):
- "Shareable if same AMT" → Can share (if same AMT and same container)
- "Not shareable" → Separate bottles required, no sharing allowed
- "N/A" → Treat as not shareable (separate bottles)

STEP 5 — VOLUME CALCULATION
For each shareable subgroup:
1. Extract bottle capacity from container_name (e.g., "390 ml" → 390)
2. Sum minimal_sample for all tests in group
3. Compare:
   - If total_mrv ≤ capacity → 1 bottle sufficient
   - If total_mrv > capacity → bottles_needed = CEILING(total_mrv / capacity)

IMPORTANT RULES:
- NEVER mix parameters across different AMT codes
- NEVER mix parameters with different container names
- NEVER assume bottle capacity - extract from container_name
- Always use minimal_sample for calculation
- If capacity cannot be extracted → report as unknown

Return JSON with this exact format:
{{
  "total_bottles_needed": <number>,
  "bottles_without_sharing": <number>,
  "bottles_saved": <number>,
  "container_groups": [
    {{
      "amt_code": "<code>",
      "amt_name": "<name>",
      "container_name": "<full name>",
      "container_capacity_ml": <number or null>,
      "tests": ["<test_code1>", "<test_code2>"],
      "test_names": ["<name1>", "<name2>"],
      "sharing_rule": "<rule>",
      "can_share": true/false,
      "individual_mrv": [<mrv1>, <mrv2>],
      "total_mrv": <number>,
      "unit": "<unit>",
      "bottles_needed": <number>,
      "reason": "<explanation>"
    }}
  ]
}}

Return ONLY valid JSON, no other text."""

    # Call Azure OpenAI
    try:
        client = AzureOpenAI(
            azure_endpoint=get_secret("AZURE_OPENAI_ENDPOINT_4"),
            api_key=get_secret("AZURE_OPENAI_API_KEY_4"),
            api_version=get_secret("AZURE_OPENAI_API_VERSION_4")
        )

        response = client.chat.completions.create(
            model=get_secret("AZURE_OPENAI_MODEL_4"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        result_text = response.choices[0].message.content

        # Parse JSON response
        try:
            result = json.loads(result_text)
            result["status"] = "success"
            result["tests_not_found"] = tests_not_found
            return result
        except json.JSONDecodeError:
            return {
                "status": "success",
                "raw_analysis": result_text,
                "tests_not_found": tests_not_found
            }
    except Exception as e:
        logger.error(f"get_container_requirements_for_tests error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "tests_not_found": tests_not_found
        }
