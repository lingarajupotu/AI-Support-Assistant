
import pandas as pd
from datetime import datetime, timezone
DATA_PATH = r"C:\Users\Linga Raju\Downloads\AI_Intern_Candidate_Pack_2026-11-02\data"

payments = pd.read_csv(DATA_PATH + r"\payments.csv")
refunds = pd.read_csv(DATA_PATH + r"\refunds.csv")
deliveries = pd.read_csv(DATA_PATH + r"\deliveries.csv")


def verify_order(issue, order_id):

    if issue in ["DOUBLE_CHARGE", "PAYMENT_FAILURES"]:

        records = payments[payments["order_id"] == order_id].copy()

        if records.empty:
            return result("NEEDS_INFORMATION",
                          "No payment records found for this order.")

        if issue == "DOUBLE_CHARGE":

            successful = records[records["status"] == "SUCCESS"]

            for i in range(len(successful)):
                for j in range(i + 1, len(successful)):

                    p1 = successful.iloc[i]
                    p2 = successful.iloc[j]

                    if (p1["amount_cents"] == p2["amount_cents"]
                        and pd.notna(p1["provider_ref"])
                        and pd.notna(p2["provider_ref"])
                        and p1["provider_ref"] != p2["provider_ref"]):

                        return result(
                            "SIGNAL_FOUND",
                            "Two successful payments with equal amounts "
                            "and different transaction references were found.",
                            [p1.to_dict(), p2.to_dict()]
                        )

            return result(
                "NOT_VERIFIED",
                "No qualifying duplicate successful payment pair was found."
            )

        if issue == "PAYMENT_FAILURES":

            failed = records[records["status"] == "FAILED"].copy()

            failed["timestamp"] = pd.to_datetime(
                failed["timestamp"], utc=True
            )

            failed = failed.sort_values("timestamp")

            for i in range(len(failed)):
                for j in range(i + 1, len(failed)):
                    for k in range(j + 1, len(failed)):

                        p1 = failed.iloc[i]
                        p2 = failed.iloc[j]
                        p3 = failed.iloc[k]

                        duration = (
                            p3["timestamp"] - p1["timestamp"]
                        ).total_seconds()

                        if duration <= 600:
                            return result(
                                "SIGNAL_FOUND",
                                "Three failed payment attempts "
                                "occurred within ten minutes.",
                                [
                                    p1.drop(labels="timestamp").to_dict()
                                    | {"timestamp": p1["timestamp"].isoformat()},
                                    p2.drop(labels="timestamp").to_dict()
                                    | {"timestamp": p2["timestamp"].isoformat()},
                                    p3.drop(labels="timestamp").to_dict()
                                    | {"timestamp": p3["timestamp"].isoformat()}
                                ]
                            )

            return result(
                "NOT_VERIFIED",
                "No three failed payment attempts within ten minutes were found."
            )

    elif issue == "REFUND_STATUS":

        records = refunds[refunds["order_id"] == order_id]

        if records.empty:
            return result(
                "NEEDS_INFORMATION",
                "No refund record was found for this order."
            )

        return result(
            "RECORD_FOUND",
            "A refund record exists. Its recorded status is "
            + records.iloc[0]["status"] + ".",
            [records.iloc[0].to_dict()]
        )

    elif issue == "DELIVERY_STATUS":

        records = deliveries[deliveries["order_id"] == order_id]

        if records.empty:
            return result(
                "NEEDS_INFORMATION",
                "No delivery record was found for this order."
            )

        delivery = records.iloc[0]
        reference_time = datetime(
            2026, 11, 2, 12, 0, tzinfo=timezone.utc
        )

        if delivery["status"] == "IN_TRANSIT":

            expected = pd.to_datetime(
                delivery["expected_by"], utc=True
            ).to_pydatetime()

            if reference_time > expected:
                return result(
                    "SIGNAL_FOUND",
                    "The delivery is in transit and past its expected deadline.",
                    [delivery.to_dict()]
                )

        return result(
            "RECORD_FOUND",
            "A delivery record exists. Current status: "
            + delivery["status"] + ".",
            [delivery.to_dict()]
        )

    return result("OUT_OF_SCOPE", "Unsupported issue category.")


def result(status, explanation, evidence=None):
    return {
        "status": status,
        "explanation": explanation,
        "evidence": evidence if evidence is not None else []
    }
