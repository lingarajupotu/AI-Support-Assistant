
import re
import json

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from llm_service import understand_query, generate_reply
from verification import verify_order

app = FastAPI(title="AI Support Assistant")


class QueryRequest(BaseModel):
    query: str


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.post("/ask")
def ask_assistant(request: QueryRequest):

    query = request.query.strip()

    if not query:
        raise HTTPException(400, "Please enter a customer query.")

    try:
        # Step 1: Understand customer query
        intent = understand_query(query)

        print("Gemini response:", intent)

        if not isinstance(intent, dict):
            raise ValueError("Invalid response from Gemini")

        issue = intent.get("issue")
        order_id = intent.get("order_id")

        valid_issues = [
            "DOUBLE_CHARGE",
            "PAYMENT_FAILURES",
            "REFUND_STATUS",
            "DELIVERY_STATUS"
        ]

        if issue == "OUT_OF_SCOPE":
            return {
                "status": "OUT_OF_SCOPE",
                "reply": "This request is outside the supported payment, refund and delivery services.",
                "evidence": []
            }

        if issue not in valid_issues:
            return {
                "status": "ERROR",
                "reply": "Unable to identify the customer issue. Please try again.",
                "evidence": []
            }

        # Step 2: Validate order ID
        ids = set(re.findall(r"\bORD-\d{4}\b", query.upper()))

        if len(ids) != 1:
            return {
                "status": "NEEDS_INFORMATION",
                "reply": "Please provide exactly one valid order ID.",
                "evidence": []
            }

        if not isinstance(order_id, str) or order_id.upper() != next(iter(ids)):
            return {
                "status": "NEEDS_INFORMATION",
                "reply": "The identified order ID is missing or does not match your query. Please confirm your order ID.",
                "evidence": []
            }

        # Step 3: Verify records using Python
        findings = verify_order(issue, order_id.upper())

        # Convert Pandas values into JSON-compatible values
        findings = json.loads(json.dumps(findings, default=str))

        # Step 4: Generate customer-facing response
        reply = generate_reply(
            query,
            issue,
            order_id,
            findings
        )

        return {
            "order_id": order_id.upper(),
            "issue": issue,
            "status": findings["status"],
            "explanation": findings["explanation"],
            "reply": reply,
            "evidence": findings["evidence"]
        }

    except Exception as e:
        import traceback
        traceback.print_exc()

        return {
            "status": "ERROR",
            "reply": str(e),
            "evidence": []
        }


app.mount("/static", StaticFiles(directory="static"), name="static")
