const form = document.querySelector("#trip-form");
const messageField = document.querySelector("#trip-message");
const submitButton = document.querySelector("#submit-button");
const resultSection = document.querySelector("#result-section");
const tripResult = document.querySelector("#trip-result");
const errorMessage = document.querySelector("#error-message");
const threadStorageKey = "tripmate-thread-id";

function renderAnswer(text) {
  const container = document.querySelector("#answer");
  container.replaceChildren();

  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    const isHeading = /^\**\s*(?:\d+[.)]\s*)?(Trip Summary|Flight Information|Hotel Suggestions|Day By Day Itinerary|Estimated Budget|Final Recommendations)\s*:?\**\s*$/i.test(trimmed);
    const element = document.createElement(isHeading ? "h3" : "p");
    element.textContent = trimmed.replace(/\*\*/g, "");
    container.append(element);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageField.value.trim();
  if (!message) {
    messageField.focus();
    return;
  }

  resultSection.hidden = false;
  tripResult.hidden = true;
  errorMessage.hidden = true;
  submitButton.disabled = true;
  submitButton.querySelector(".button-label").textContent = "Planning your trip...";

  try {
    const response = await fetch("/api", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        thread_id: sessionStorage.getItem(threadStorageKey),
      }),
    });
    const data = await response.json();
    if (!response.ok || !data.success) {
      throw new Error(data.error || `Trip planning failed (${response.status}). Please try again.`);
    }

    if (data.thread_id) sessionStorage.setItem(threadStorageKey, data.thread_id);
    renderAnswer(data.answer || "Your plan is ready, but no summary was returned.");
    document.querySelector("#flight-results").textContent = data.flight_results || "No flight details were returned.";
    document.querySelector("#hotel-results").textContent = data.hotel_results || "No hotel suggestions were returned.";
    document.querySelector("#itinerary").textContent = data.itinerary || "No separate itinerary was returned.";
    tripResult.hidden = false;
  } catch (error) {
    errorMessage.textContent = error instanceof Error ? error.message : "Something went wrong. Please try again.";
    errorMessage.hidden = false;
  } finally {
    submitButton.disabled = false;
    submitButton.querySelector(".button-label").textContent = "Plan my trip";
    resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }
});

document.querySelector("#new-trip-button").addEventListener("click", () => {
  messageField.value = "";
  messageField.focus();
  window.scrollTo({ top: 0, behavior: "smooth" });
});

document.querySelector("#copy-button").addEventListener("click", async (event) => {
  const copyButton = event.currentTarget;
  const answer = document.querySelector("#answer").innerText;
  try {
    await navigator.clipboard.writeText(answer);
    copyButton.textContent = "Copied!";
    window.setTimeout(() => { copyButton.textContent = "Copy plan"; }, 1800);
  } catch {
    errorMessage.textContent = "Could not copy the plan. Please select and copy the text manually.";
    errorMessage.hidden = false;
  }
});