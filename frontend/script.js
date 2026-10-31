
// Clean AI-generated Markdown for the existing plain-text chat UI.
function formatAIAnswer(text) {
    return String(text || "")
        .replace(/\r\n/g, "\n")
        .replace(/^\s*\|[\s:|-]+\|\s*$/gm, "")
        .replace(/^\s*\|(.+)\|\s*$/gm, (_, cells) =>
            cells.split("|").map(cell => cell.trim()).join("  |  ")
        )
        .replace(/\*\*(.*?)\*\*/g, "$1")
        .replace(/`([^`]+)`/g, "$1")
        .replace(/^#{1,6}\s+/gm, "")
        .replace(/\n{3,}/g, "\n\n")
        .trim();
}


const API_URL = "https://enterprise-genai-platform-6xrg.onrender.com";

// Sidebar navigation
const navButtons = document.querySelectorAll(".nav-item");
const pages = document.querySelectorAll(".page");

navButtons.forEach((button) => {
    button.addEventListener("click", () => {
        const selectedPage = button.dataset.page;

        navButtons.forEach((item) => {
            item.classList.remove("active");
        });

        pages.forEach((page) => {
            page.classList.remove("active");
        });

        button.classList.add("active");

        document
            .getElementById(`${selectedPage}-page`)
            .classList.add("active");
    });
});

// AI Chat
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatMessages = document.getElementById("chat-messages");
const sendButton = document.getElementById("send-button");

function addMessage(text, sender) {
    const message = document.createElement("div");

    message.className = `message ${sender}`;
    message.textContent = text;

    chatMessages.appendChild(message);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const question = chatInput.value.trim();

    if (!question) {
        return;
    }

    addMessage(question, "user");

    chatInput.value = "";
    sendButton.disabled = true;
    sendButton.textContent = "Thinking...";

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question
            })
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        let answer = data.answer || data.response || data.reply || "No answer received.";

        if (data.sources && data.sources.length > 0) {
            const sourceNames = [
                ...new Set(
                    data.sources
                        .map((source) => source.source)
                        .filter(Boolean)
                )
            ];

            if (sourceNames.length > 0) {
                answer += "\n\nSources: " + sourceNames.join(", ");
            }
        }

        addMessage(formatAIAnswer(answer), "assistant");

    } catch (error) {
        addMessage(
            "Could not connect to the cloud AI service. Please try again.",
            "assistant"
        );

        console.error(error);

    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "Send";
        chatInput.focus();
    }
});



// Knowledge Base - PDF Upload and Document List

const uploadForm = document.getElementById("upload-form");
const pdfFile = document.getElementById("pdf-file");
const uploadButton = document.getElementById("upload-button");
const uploadStatus = document.getElementById("upload-status");
const documentsList = document.getElementById("documents-list");
const refreshButton = document.getElementById("refresh-documents");

// Load indexed documents from FastAPI
async function loadDocuments() {
    documentsList.textContent = "Loading documents...";

    try {
        const response = await fetch(`${API_URL}/documents`);

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        documentsList.replaceChildren();

        const documents = Array.isArray(data)
            ? data
            : (data.documents || []);

        if (documents.length === 0) {
            documentsList.textContent = "No documents uploaded yet.";
            return;
        }

        const summary = document.createElement("p");
        summary.textContent =
            `Total documents: ${documents.length}`;

        documentsList.appendChild(summary);

        documents.forEach((documentInfo) => {
            const item = document.createElement("div");
            item.className = "document-item";

            item.textContent =
                `📄 ${documentInfo.filename} — ${documentInfo.chunks} chunks`;

            documentsList.appendChild(item);
        });

    } catch (error) {
        documentsList.textContent =
            "Unable to load documents. Check FastAPI server.";

        console.error(error);
    }
}

// Upload a PDF to the knowledge base
uploadForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const file = pdfFile.files[0];

    if (!file) {
        uploadStatus.textContent = "Please select a PDF.";
        return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {
        uploadStatus.textContent = "Only PDF files are allowed.";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    uploadButton.disabled = true;
    uploadButton.textContent = "Uploading...";
    uploadStatus.textContent = "Uploading and indexing PDF...";

    try {
        const response = await fetch(`${API_URL}/documents/upload`, {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                typeof result.detail === "string"
                    ? result.detail
                    : `Upload failed: ${response.status}`
            );
        }

        uploadStatus.textContent =
            `Success! ${result.filename} indexed (${result.total_chunks} chunks).`;

        uploadForm.reset();
        await loadDocuments();

    } catch (error) {
        uploadStatus.textContent = error.message;
        console.error(error);

    } finally {
        uploadButton.disabled = false;
        uploadButton.textContent = "Upload Document";
    }
});

// Refresh button
refreshButton.addEventListener("click", loadDocuments);

// Load documents when Knowledge Base is opened
document.querySelector('[data-page="documents"]')
    .addEventListener("click", loadDocuments);


    
// -------------------------------------
// IT Ticket Management
// -------------------------------------

const ticketForm = document.getElementById("ticket-form");
const ticketTitle = document.getElementById("ticket-title");
const ticketDescription = document.getElementById("ticket-description");
const ticketStatus = document.getElementById("ticket-status");
const createTicketButton = document.getElementById("create-ticket-button");
const ticketsList = document.getElementById("tickets-list");
const refreshTicketsButton = document.getElementById("refresh-tickets");


// Show saved AI analysis
function displayTicketAnalysis(container, rawAnalysis) {

    let analysis;

    try {
        analysis = typeof rawAnalysis === "string"
            ? JSON.parse(rawAnalysis)
            : rawAnalysis;
    } catch (error) {
        container.textContent = "Could not read saved AI analysis.";
        return;
    }

    if (!analysis || typeof analysis !== "object") {
        container.textContent = "No valid AI analysis available.";
        return;
    }

    container.replaceChildren();

    const heading = document.createElement("h4");
    heading.textContent = "AI Analysis (Engineer Review Required)";
    container.appendChild(heading);

    const fields = [
        ["Category", analysis.category],
        ["Suggested Priority", (analysis.suggested_priority || analysis.priority)],
        ["Reasoning", analysis.reasoning],
        ["Escalation", analysis.escalation]
    ];

    fields.forEach(([label, value]) => {
        const paragraph = document.createElement("p");
        paragraph.textContent = `${label}: ${value || "Not provided"}`;
        container.appendChild(paragraph);
    });

    const stepsHeading = document.createElement("p");
    stepsHeading.textContent = "Suggested Troubleshooting Steps:";
    container.appendChild(stepsHeading);

    const stepsList = document.createElement("ol");

    if (Array.isArray(analysis.troubleshooting_steps)) {
        analysis.troubleshooting_steps.forEach((step) => {
            const item = document.createElement("li");
            item.textContent = String(step);
            stepsList.appendChild(item);
        });
    }

    container.appendChild(stepsList);


    
// -------------------------------------
// Display flagged risky AI actions
// -------------------------------------

if (
    Array.isArray(analysis.flagged_steps) &&
    analysis.flagged_steps.length > 0
) {
    const warningBox = document.createElement("div");
    warningBox.className = "ai-safety-warning";

    const warningHeading = document.createElement("h4");
    warningHeading.textContent =
        "⚠️ Risky Actions — Engineer Approval Required";

    warningBox.appendChild(warningHeading);

    const flaggedList = document.createElement("ul");

    analysis.flagged_steps.forEach((item) => {
        const listItem = document.createElement("li");

        const reasons = Array.isArray(item.reasons)
            ? item.reasons.join(", ")
            : "Requires review";

        listItem.textContent =
            `${item.step} — Reason: ${reasons}`;

        flaggedList.appendChild(listItem);
    });

    warningBox.appendChild(flaggedList);
    container.appendChild(warningBox);
}


    const warning = document.createElement("p");
    warning.textContent =
        "AI suggestions are unverified. Do not restart production systems " +
        "or change permissions without authorized engineer approval.";
    container.appendChild(warning);
}


// Load tickets from FastAPI
async function loadTickets() {
    ticketsList.textContent = "Loading tickets...";

    try {
        const response = await fetch(`${API_URL}/tickets`);

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        ticketsList.replaceChildren();

        if (
            (Array.isArray(data) ? data : (data.tickets || [])).length === 0
        ) {
            ticketsList.textContent = "No tickets created yet.";
            return;
        }

        const summary = document.createElement("p");
        summary.textContent = `Total tickets: ${
            Array.isArray(data)
                ? data.length
                : (data.total_tickets ?? (data.tickets || []).length)
        }`;
        ticketsList.appendChild(summary);

        (Array.isArray(data) ? data : (data.tickets || [])).forEach((ticket) => {
        if (typeof ticket.ai_analysis === "string") {
            try {
                ticket.ai_analysis = JSON.parse(ticket.ai_analysis);
            } catch (error) {
                ticket.ai_analysis = null;
            }
        }
            const card = document.createElement("div");
            card.className = "ticket-card";

            const title = document.createElement("h4");
            title.textContent = `#${ticket.id} — ${ticket.title}`;

            const description = document.createElement("p");
            description.textContent = ticket.description;

            const status = document.createElement("p");
            status.textContent =
                `Status: ${ticket.status} | ` +
                `Category: ${(ticket.category || ticket.ai_analysis?.category || 'Unclassified')} | ` +
                `Priority: ${(ticket.priority || ticket.ai_analysis?.priority || 'Not assigned')}`;

            const analyzeButton = document.createElement("button");
            analyzeButton.type = "button";
            analyzeButton.textContent = "Analyze with AI";

            const analysisContainer = document.createElement("div");
            analysisContainer.className = "ticket-analysis";

           
card.appendChild(title);
card.appendChild(description);
card.appendChild(status);
card.appendChild(analyzeButton);
card.appendChild(analysisContainer);


card.appendChild(analysisContainer);

// Engineer Review Panel
const reviewPanel = createEngineerReviewPanel(ticket);
card.appendChild(reviewPanel);

// Ticket Status Management Panel
const statusPanel = createTicketStatusPanel(ticket);
card.appendChild(statusPanel);

            


            if (ticket.ai_analysis) {
                displayTicketAnalysis(
                    analysisContainer,
                    ticket.ai_analysis
                );
            }

            analyzeButton.addEventListener("click", async () => {
                analyzeButton.disabled = true;
                analyzeButton.textContent = "Analyzing...";

                try {
                    const response = await fetch(
                        `${API_URL}/tickets/${ticket.id}/analyze`,
                        { method: "POST" }
                    );

                    if (!response.ok) {
                        throw new Error(
                            `AI analysis failed: ${response.status}`
                        );
                    }

                    
const result = await response.json();

displayTicketAnalysis(
    analysisContainer,
    result.ai_analysis
);

await loadTickets();


                } catch (error) {
                    analysisContainer.textContent = error.message;
                    console.error(error);

                } finally {
                    analyzeButton.disabled = false;
                    analyzeButton.textContent = "Analyze with AI";
                }
            });

            ticketsList.appendChild(card);
        });

    } catch (error) {
        ticketsList.textContent =
            "Could not load tickets. Check FastAPI server.";
        console.error(error);
    }
}


// Create a new ticket
ticketForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const title = ticketTitle.value.trim();
    const description = ticketDescription.value.trim();

    if (!title || !description) {
        ticketStatus.textContent =
            "Please enter a title and description.";
        return;
    }

    createTicketButton.disabled = true;
    createTicketButton.textContent = "Creating...";
    ticketStatus.textContent = "Creating ticket...";

    try {
        const response = await fetch(`${API_URL}/tickets`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                title: title,
                description: description
            })
        });

        if (!response.ok) {
            throw new Error(
                `Ticket creation failed: ${response.status}`
            );
        }

        const result = await response.json();

        ticketStatus.textContent =
            `Ticket #${(result.ticket || result).id} created successfully!`;

        ticketForm.reset();

        await loadTickets();

    } catch (error) {
        ticketStatus.textContent = error.message;
        console.error(error);

    } finally {
        createTicketButton.disabled = false;
        createTicketButton.textContent = "Create Ticket";
    }
});


// Refresh tickets button
refreshTicketsButton.addEventListener("click", loadTickets);


// Load tickets when IT Tickets page is opened
document.querySelector('[data-page="tickets"]')
    .addEventListener("click", loadTickets);



    
/* ==========================================
   ENGINEER REVIEW & APPROVAL WORKFLOW
   ========================================== */

// Create Engineer Review panel for one ticket
function createEngineerReviewPanel(ticket) {
    const panel = document.createElement("div");
    panel.className = "engineer-review-panel";

    panel.style.marginTop = "16px";
    panel.style.padding = "16px";
    panel.style.border = "1px solid #475569";
    panel.style.borderRadius = "10px";

    const heading = document.createElement("h4");
    heading.textContent = "Engineer Review";
    panel.appendChild(heading);

    const status = document.createElement("p");
    status.textContent =
        "Review Status: " +
        (ticket.review_status || "Pending");

    panel.appendChild(status);

    if (ticket.reviewed_by) {
        const reviewer = document.createElement("p");
        reviewer.textContent =
            "Reviewed By: " + ticket.reviewed_by;
        panel.appendChild(reviewer);
    }

    if (ticket.review_notes) {
        const savedNotes = document.createElement("p");
        savedNotes.textContent =
            "Previous Notes: " + ticket.review_notes;
        panel.appendChild(savedNotes);
    }

    // Only show review form after AI analysis
    if (!ticket.ai_analysis) {
        const message = document.createElement("p");
        message.textContent =
            "Run AI analysis before engineer review.";
        panel.appendChild(message);
        return panel;
    }

    const nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.placeholder = "Engineer name";
    nameInput.style.display = "block";
    nameInput.style.width = "100%";
    nameInput.style.marginBottom = "10px";
    nameInput.style.padding = "10px";

    const notesInput = document.createElement("textarea");
    notesInput.placeholder = "Review notes (required)";
    notesInput.rows = 3;
    notesInput.style.display = "block";
    notesInput.style.width = "100%";
    notesInput.style.marginBottom = "10px";
    notesInput.style.padding = "10px";

    const approveButton = document.createElement("button");
    approveButton.type = "button";
    approveButton.textContent = "Approve";
    approveButton.style.marginRight = "10px";
    approveButton.style.backgroundColor = "#15803d";
    approveButton.style.color = "white";

    const rejectButton = document.createElement("button");
    rejectButton.type = "button";
    rejectButton.textContent = "Reject";
    rejectButton.style.backgroundColor = "#b91c1c";
    rejectButton.style.color = "white";

    const feedback = document.createElement("p");
    feedback.style.marginTop = "12px";

    async function submitReview(decision) {
        const reviewedBy = nameInput.value.trim();
        const notes = notesInput.value.trim();

        if (!reviewedBy || !notes) {
            feedback.textContent =
                "Engineer name and review notes are required.";
            return;
        }

        approveButton.disabled = true;
        rejectButton.disabled = true;
        feedback.textContent = "Saving review...";

        try {
            const response = await fetch(
                `${API_URL}/tickets/${ticket.id}/review`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        decision: decision,
                        reviewed_by: reviewedBy,
                        notes: notes
                    })
                }
            );

            const result = await response.json();

            if (!response.ok) {
                throw new Error(
                    typeof result.detail === "string"
                        ? result.detail
                        : `Review failed: ${response.status}`
                );
            }

            status.textContent =
                "Review Status: " + result.review_status;

            feedback.textContent =
                "Review saved successfully!";

            // Reload tickets to show saved review data
            await loadTickets();

        } catch (error) {
            feedback.textContent = error.message;
            console.error(error);

        } finally {
            approveButton.disabled = false;
            rejectButton.disabled = false;
        }
    }

    approveButton.addEventListener("click", () => {
        submitReview("Approved");
    });

    rejectButton.addEventListener("click", () => {
        submitReview("Rejected");
    });

    panel.appendChild(nameInput);
    panel.appendChild(notesInput);
    panel.appendChild(approveButton);
    panel.appendChild(rejectButton);
    panel.appendChild(feedback);

    return panel;
}




/* =========================================
   Ticket Status Management
========================================= */

function createTicketStatusPanel(ticket) {
    const panel = document.createElement("div");
    panel.className = "ticket-status-panel";

    const heading = document.createElement("h4");
    heading.textContent = "Ticket Status Management";
    panel.appendChild(heading);

    const currentStatus = document.createElement("p");
    currentStatus.textContent =
        `Current Status: ${ticket.status || "Open"}`;

    panel.appendChild(currentStatus);

    const buttonsContainer = document.createElement("div");
    buttonsContainer.className = "ticket-status-buttons";

    const statusOptions = [
        { label: "Start Progress", status: "In Progress" },
        { label: "Resolve Ticket", status: "Resolved" },
        { label: "Close Ticket", status: "Closed" },
    ];

    statusOptions.forEach((option) => {
        const button = document.createElement("button");

        button.type = "button";
        button.textContent = option.label;

        button.style.marginRight = "8px";
        button.style.marginBottom = "8px";
        button.style.padding = "8px 12px";
        button.style.cursor = "pointer";

        // Prevent redundant status updates
        button.disabled = ticket.status === option.status;

        button.addEventListener("click", async () => {
            const confirmation = window.confirm(
                `Change Ticket #${ticket.id} status to "${option.status}"?`
            );

            if (!confirmation) {
                return;
            }

            button.disabled = true;

            try {
                const response = await fetch(
                    `${API_URL}/tickets/${ticket.id}/status`,
                    {
                        method: "PATCH",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({
                            status: option.status,
                        }),
                    }
                );

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(
                        errorData.detail ||
                        "Could not update ticket status."
                    );
                }

                const result = await response.json();

                alert(
                    `Ticket #${ticket.id}: ${(result.new_status || result.status)}`
                );

                // Refresh ticket cards with updated status
                await loadTickets();

            } catch (error) {
                console.error(
                    "Ticket status update failed:",
                    error
                );

                alert(
                    `Status update failed: ${error.message}`
                );

                button.disabled = false;
            }
        });

        buttonsContainer.appendChild(button);
    });

    panel.appendChild(buttonsContainer);

    return panel;
}




/* =====================================
   Dashboard Analytics
===================================== */

async function loadDashboardStats() {
    const container = document.getElementById("dashboard-stats");

    if (!container) {
        return;
    }

    container.textContent = "Loading dashboard...";

    try {
        const response = await fetch(
            `${API_URL}/dashboard/stats`
        );

        if (!response.ok) {
            throw new Error("Failed to load dashboard statistics.");
        }

        const stats = await response.json();

        /* CLOUD REVIEW STATS COMPATIBILITY */
        if (
            stats.pending_reviews === undefined ||
            stats.approved_reviews === undefined ||
            stats.rejected_reviews === undefined
        ) {
            const ticketResponse = await fetch(`${API_URL}/tickets`);

            if (ticketResponse.ok) {
                const ticketData = await ticketResponse.json();
                const tickets = Array.isArray(ticketData)
                    ? ticketData
                    : (ticketData.tickets || []);

                const analyzedTickets = tickets.filter(
                    (ticket) => Boolean(ticket.ai_analysis)
                );

                stats.pending_reviews = analyzedTickets.filter(
                    (ticket) =>
                        !ticket.review_status ||
                        ticket.review_status === "Pending"
                ).length;

                stats.approved_reviews = analyzedTickets.filter(
                    (ticket) => ticket.review_status === "Approved"
                ).length;

                stats.rejected_reviews = analyzedTickets.filter(
                    (ticket) => ticket.review_status === "Rejected"
                ).length;
            }
        }

        const cards = [
            ["Total Tickets", stats.total_tickets],
            ["Open Tickets", stats.open_tickets],
            ["In Progress", stats.in_progress_tickets],
            ["Resolved Tickets", stats.resolved_tickets],
            ["Closed Tickets", stats.closed_tickets],
            ["Pending Reviews", stats.pending_reviews],
            ["Approved Reviews", stats.approved_reviews],
            ["Rejected Reviews", stats.rejected_reviews],
        ];

        container.innerHTML = "";

        cards.forEach(([label, value]) => {
            const card = document.createElement("div");
            card.className = "dashboard-stat-card";

            const heading = document.createElement("h3");
            heading.textContent = label;

            const number = document.createElement("p");
            number.textContent = value ?? 0;

            card.appendChild(heading);
            card.appendChild(number);
            container.appendChild(card);
        });

    } catch (error) {
        console.error("Dashboard error:", error);
        container.textContent =
            "Unable to load dashboard. Check backend connection.";
    }
}




/* =====================================
   Dashboard Navigation Integration
===================================== */

document
    .querySelector('[data-page="dashboard"]')
    ?.addEventListener("click", () => {
        loadDashboardStats();
    });

document
    .getElementById("refresh-dashboard")
    ?.addEventListener("click", () => {
        loadDashboardStats();
    });
