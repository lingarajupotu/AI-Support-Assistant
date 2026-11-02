
async function submitQuery() {

    const query = document.getElementById("query").value.trim();
    const button = document.getElementById("submitBtn");
    const results = document.getElementById("results");
    const error = document.getElementById("error");

    error.textContent = "";
    results.classList.add("hidden");

    if (!query) {
        error.textContent = "Please enter a customer query.";
        return;
    }

    button.disabled = true;
    button.textContent = "Processing...";

    try {

        const response = await fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ query: query })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Request failed");
        }

        document.getElementById("orderId").textContent =
            data.order_id || "-";

        document.getElementById("issue").textContent =
            data.issue || "-";

        document.getElementById("status").textContent =
            data.status || "-";

        document.getElementById("explanation").textContent =
            data.explanation || "-";

        document.getElementById("reply").textContent =
            data.reply || "No response generated.";

        document.getElementById("evidence").textContent =
            data.evidence && data.evidence.length > 0
            ? JSON.stringify(data.evidence, null, 2)
            : "No supporting records.";

        results.classList.remove("hidden");

    } catch (err) {

        error.textContent = "Error: " + err.message;

    } finally {

        button.disabled = false;
        button.textContent = "Submit Query";

    }
}
