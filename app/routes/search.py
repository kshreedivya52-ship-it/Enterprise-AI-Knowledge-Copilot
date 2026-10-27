from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from langsmith import traceable

from app.core.auth import get_current_user, CurrentUser
from app.core.database import get_db
from app.core.vector_db import query_hybrid_search
from app.core.reranker import rerank_documents
from app.core.llm import generate_grounded_answer
from app.crud.chat import (
    get_or_create_conversation,
    add_chat_message,
    get_conversation_messages,
)

router = APIRouter(prefix="/search", tags=["search"])


def format_history_for_prompt(messages) -> str:
    """Formats raw database chat messages into a clean readable transcript for GPT-4o."""
    if not messages:
        return "No prior conversation history."
    formatted = []
    for msg in messages:
        role_label = "User" if msg.role == "user" else "Assistant"
        formatted.append(f"{role_label}: {msg.content}")
    return "\n".join(formatted)


import re
from typing import Optional, List, Tuple

DEPARTMENT_KEYWORDS = {
    "finance": [
        "finance", "financial", "revenue", "ebitda", "budget", "budgets", "invoice", "invoices",
        "reimbursement", "accounts payable", "annual report", "expense", "expenses",
        "purchase approval", "fiscal year", "profit", "balance sheet", "p&l", "tax", "audit", "treasury"
    ],
    "engineering": [
        "architecture", "api", "apis", "database design", "deployment", "kubernetes",
        "troubleshooting", "microservices", "system design", "technical manual", "runbook",
        "docker", "cluster", "citus", "envoy", "kafka", "redis", "schema"
    ],
    "legal": [
        "legal", "compliance", "agreement", "agreements", "contract", "contracts",
        "nda", "non-disclosure", "vendor agreement", "gdpr", "privacy policy",
        "anti-bribery", "regulatory", "master service", "retention policy", "fcpa", "ccpa", "arbitration"
    ],
    "hr": [
        "hr policies", "human resources", "onboarding guide", "leave policy", "attendance policy",
        "salary band", "salary bands", "severance", "pip", "performance improvement", "parental leave"
    ],
}

DEPARTMENT_DOCS = {
    "finance": [
        "annual_financial_report_2026", "expense_reimbursement_policy",
        "invoice_processing_guidelines", "department_budget_2026", "purchase_approval_policy"
    ],
    "engineering": [
        "system_architecture", "api_documentation", "database_design",
        "software_deployment_guide", "troubleshooting_manual"
    ],
    "legal": [
        "master_service_agreement", "non_disclosure_agreement", "vendor_agreement",
        "client_service_contract", "partnership_agreement", "legal_compliance_policy",
        "data_protection_and_privacy_policy", "regulatory_compliance_manual",
        "records_retention_policy", "anti_bribery_and_corruption_policy"
    ],
    "hr": [
        "hr_policies_2026", "leave_and_attendance_policy", "employee_onboarding_guide"
    ],
}

CANONICAL_DOC_NAMES = {
    "annual_financial_report_2026": "Annual_Financial_Report_2026.pdf",
    "expense_reimbursement_policy": "Expense_Reimbursement_Policy.pdf",
    "invoice_processing_guidelines": "Invoice_Processing_Guidelines.docx",
    "department_budget_2026": "Department_Budget_2026.xlsx",
    "purchase_approval_policy": "Purchase_Approval_Policy.pdf",
    "system_architecture": "System_Architecture.pdf",
    "api_documentation": "API_Documentation.docx",
    "database_design": "Database_Design.pdf",
    "software_deployment_guide": "Software_Deployment_Guide.md",
    "troubleshooting_manual": "Troubleshooting_Manual.pdf",
    "master_service_agreement": "Master_Service_Agreement.pdf",
    "non_disclosure_agreement": "Non_Disclosure_Agreement_NDA.pdf",
    "vendor_agreement": "Vendor_Agreement.pdf",
    "client_service_contract": "Client_Service_Contract.pdf",
    "partnership_agreement": "Partnership_Agreement.pdf",
    "legal_compliance_policy": "Legal_Compliance_Policy.pdf",
    "data_protection_and_privacy_policy": "Data_Protection_and_Privacy_Policy.pdf",
    "regulatory_compliance_manual": "Regulatory_Compliance_Manual.pdf",
    "records_retention_policy": "Records_Retention_Policy.pdf",
    "anti_bribery_and_corruption_policy": "Anti_Bribery_and_Corruption_Policy.pdf",
    "hr_policies_2026": "HR_Policies_2026.pdf",
    "leave_and_attendance_policy": "Leave_and_Attendance_Policy.pdf",
    "employee_onboarding_guide": "Employee_Onboarding_Guide.docx",
}


def detect_restricted_department(
    query_text: str,
    user_department: str,
    user_role: str,
) -> Optional[Tuple[str, List[str]]]:
    """
    Detects if the user is asking for documents or operational data belonging to a
    department that their assigned role is not authorized to access.
    """
    if user_role == "admin":
        return None

    user_dept = (user_department or "general").lower().strip()
    user_allowed = {user_dept, "general"}
    q_norm = query_text.lower().replace(" ", "_").replace("-", "_").replace(".", "_")
    q_lower = query_text.lower()

    # 1. Exact document name / slug matches
    for dept, doc_slugs in DEPARTMENT_DOCS.items():
        if dept not in user_allowed:
            for slug in doc_slugs:
                if slug in q_norm or slug.replace("_", " ") in q_lower:
                    return dept, [slug]

    # 2. Domain keywords with regex word boundaries
    for dept, keywords in DEPARTMENT_KEYWORDS.items():
        if dept not in user_allowed:
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', q_lower):
                    unfiltered = query_hybrid_search(query_text=query_text, department=None, limit=3)
                    matched_files = [
                        h["metadata"].get("source_file") for h in unfiltered
                        if h.get("metadata", {}).get("department", "").lower() == dept
                    ]
                    return dept, matched_files

    # 3. Vector search top global match check
    unfiltered_hits = query_hybrid_search(query_text=query_text, department=None, limit=3)
    if unfiltered_hits:
        top_hit = unfiltered_hits[0]
        top_dept = top_hit.get("metadata", {}).get("department")
        if top_dept and top_dept.lower() not in user_allowed and top_dept.lower() in DEPARTMENT_KEYWORDS:
            fname = top_hit.get("metadata", {}).get("source_file")
            return top_dept.lower(), [fname] if fname else []

    return None


@router.get("")
@traceable(name="hybrid search endpoint with conversation history", run_type="chain")
async def search_endpoint(
    q: str = Query(..., min_length=1, description="Search query string"),
    session_id: Optional[str] = Query(None, description="Optional conversation session UUID"),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stateful RAG endpoint:
    1. Loads or creates a conversation session in PostgreSQL for the user.
    2. Fetches past messages to inject context window into GPT-4o.
    3. Performs RBAC permission checks against requested departmental documents.
    4. Performs hybrid retrieval + reranking.
    5. Generates grounded answer with citations.
    6. Saves user question & assistant response + citations to PostgreSQL.
    """
    try:
        dept_filter = None if user.role == "admin" else user.department

        # 1. Fetch or create conversation thread in PostgreSQL
        conversation = await get_or_create_conversation(
            db=db,
            user_id=user.sub,
            conversation_id=session_id,
            title=q[:50]  # Auto-title using first prompt snippet
        )

        # 2. RBAC Access Gate: Check if user is attempting to query restricted departmental documents
        restricted_info = detect_restricted_department(
            query_text=q,
            user_department=user.department,
            user_role=user.role
        )

        if restricted_info:
            target_dept, sample_docs = restricted_info
            dept_title = target_dept.title()
            if sample_docs:
                clean_docs = [CANONICAL_DOC_NAMES.get(d, d) for d in sample_docs if d]
                files_str = f" (such as `{', '.join(clean_docs[:2])}`)" if clean_docs else ""
            else:
                files_str = ""

            denial_answer = (
                f"🔒 **Access Restricted**: You do not have permission to access **{dept_title}** documents{files_str} "
                f"under your current role (`{user.department}`). Access to {dept_title.lower()} files, "
                f"financial records, and departmental guidelines is strictly restricted to authorized {dept_title} personnel."
            )

            # Record in PostgreSQL conversation history
            await add_chat_message(
                db=db,
                conversation_id=conversation.id,
                role="user",
                content=q
            )
            await add_chat_message(
                db=db,
                conversation_id=conversation.id,
                role="assistant",
                content=denial_answer,
                citations=[],
                extra_metadata={
                    "has_sufficient_context": False,
                    "rbac_denied": True,
                    "target_department": target_dept
                }
            )

            return {
                "session_id": conversation.id,
                "query": q,
                "user": user.sub,
                "department_filter": dept_filter or "all (admin)",
                "answer": denial_answer,
                "has_sufficient_context": False,
                "citations": [],
                "total_sources_cited": 0,
                "reranked_chunks": []
            }

        # 3. Retrieve recent message history (sliding window of last 10 messages)
        past_messages = await get_conversation_messages(
            db=db,
            conversation_id=conversation.id,
            limit=10
        )
        formatted_history = format_history_for_prompt(past_messages)

        # 4. Hybrid retrieval (Dense + Sparse) with user's RBAC filter
        results = query_hybrid_search(query_text=q, department=dept_filter)

        # 5. Rerank candidates to top 5 precision chunks
        final_results = rerank_documents(query=q, documents=results, top_n=5)

        # 6. Grounded generation with citation verification + past history context + RBAC role
        rag_response = await generate_grounded_answer(
            query=q,
            documents=final_results,
            chat_history=formatted_history,
            user_department=user.department,
            user_role=user.role
        )

        # Secondary RBAC check: If LLM output indicated insufficient context or refusal
        if not rag_response.has_sufficient_context:
            q_lower = q.lower()
            for dept, keywords in DEPARTMENT_KEYWORDS.items():
                if dept != user.department and dept != "general":
                    if any(re.search(r'\b' + re.escape(kw) + r'\b', q_lower) for kw in keywords):
                        rag_response.answer = (
                            f"🔒 **Access Restricted**: You do not have permission to access **{dept.title()}** documents "
                            f"under your current role (`{user.department}`). Access to company {dept.lower()} records "
                            f"is restricted to authorized {dept.title()} personnel."
                        )
                        break

        # 7. Save user message to PostgreSQL
        await add_chat_message(
            db=db,
            conversation_id=conversation.id,
            role="user",
            content=q
        )

        # 8. Save assistant answer & citations to PostgreSQL
        citations_json = [c.model_dump() for c in rag_response.citations]
        await add_chat_message(
            db=db,
            conversation_id=conversation.id,
            role="assistant",
            content=rag_response.answer,
            citations=citations_json,
            extra_metadata={
                "has_sufficient_context": rag_response.has_sufficient_context,
                "total_sources_cited": len(rag_response.citations)
            }
        )

        return {
            "session_id": conversation.id,
            "query": q,
            "user": user.sub,
            "department_filter": dept_filter or "all (admin)",
            "answer": rag_response.answer,
            "has_sufficient_context": rag_response.has_sufficient_context,
            "citations": rag_response.citations,
            "total_sources_cited": len(rag_response.citations),
            "reranked_chunks": final_results
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search pipeline error: {str(e)}"
        )
