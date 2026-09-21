const $ = (selector) => document.querySelector(selector);

const form = $("#copyForm");
const description = $("#description");
const descriptionCount = $("#descriptionCount");

const temperature = $("#temperature");
const temperatureValue = $("#temperatureValue");

const topP = $("#topP");
const topPValue = $("#topPValue");

const generateBtn = $("#generateBtn");
const resultSection = $("#resultSection");
const emptyState = $("#emptyState");

const subjectValue = $("#subjectValue");
const headlineValue = $("#headlineValue");
const bodyValue = $("#bodyValue");
const ctaValue = $("#ctaValue");
const hashtagsValue = $("#hashtagsValue");

const characterCount = $("#characterCount");
const resultPlatform = $("#resultPlatform");
const resultTone = $("#resultTone");
const resultTemperature = $("#resultTemperature");

const errorBox = $("#errorBox");


/* =========================
   DESCRIPTION COUNTER
========================= */

function updateDescriptionCount() {
    if (!description || !descriptionCount) return;

    descriptionCount.textContent = description.value.length;
}

if (description) {
    description.addEventListener(
        "input",
        updateDescriptionCount
    );

    updateDescriptionCount();
}


/* =========================
   TEMPERATURE
========================= */

function updateTemperature() {
    if (!temperature || !temperatureValue) return;

    temperatureValue.textContent =
        Number(temperature.value).toFixed(2);
}

if (temperature) {
    temperature.addEventListener(
        "input",
        updateTemperature
    );

    updateTemperature();
}


/* =========================
   TOP P
========================= */

function updateTopP() {
    if (!topP || !topPValue) return;

    topPValue.textContent =
        Number(topP.value).toFixed(2);
}

if (topP) {
    topP.addEventListener(
        "input",
        updateTopP
    );

    updateTopP();
}


/* =========================
   ERROR
========================= */

function showError(message) {
    if (!errorBox) {
        alert(message);
        return;
    }

    errorBox.textContent = message;
    errorBox.classList.remove("hidden");
}

function hideError() {
    if (!errorBox) return;

    errorBox.textContent = "";
    errorBox.classList.add("hidden");
}


/* =========================
   RESULT HELPERS
========================= */

function setText(element, value) {
    if (!element) return;

    element.textContent =
        value || "—";
}

function getHashtags(value) {
    if (!value) return "";

    if (Array.isArray(value)) {
        return value.join(" ");
    }

    return String(value);
}

function getCharacterCount(data) {
    if (data.character_count !== undefined) {
        return data.character_count;
    }

    const parts = [
        data.subject,
        data.headline,
        data.body,
        data.call_to_action,
        getHashtags(data.hashtags)
    ];

    return parts
        .filter(Boolean)
        .join(" ")
        .length;
}


/* =========================
   RENDER RESULT
========================= */

function renderResult(data) {
    if (!data) return;

    const platform =
        data.platform ||
        $("#platform")?.value ||
        "Instagram";

    const tone =
        data.tone ||
        $("#tone")?.value ||
        "Professional";

    setText(
        subjectValue,
        data.subject
    );

    setText(
        headlineValue,
        data.headline
    );

    setText(
        bodyValue,
        data.body
    );

    setText(
        ctaValue,
        data.call_to_action
    );

    setText(
        hashtagsValue,
        getHashtags(data.hashtags)
    );

    setText(
        characterCount,
        getCharacterCount(data)
    );

    setText(
        resultPlatform,
        platform
    );

    setText(
        resultTone,
        tone
    );

    setText(
        resultTemperature,
        Number(
            data.temperature ??
            temperature?.value ??
            0.7
        ).toFixed(2)
    );

    if (emptyState) {
        emptyState.classList.add("hidden");
    }

    if (resultSection) {
        resultSection.classList.remove("hidden");

        resultSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }

    /* Compliance notes */
    const notes =
        document.querySelector("#complianceNotes");

    if (notes) {
        const compliance =
            data.compliance_notes;

        if (Array.isArray(compliance)) {
            notes.innerHTML =
                compliance
                    .map(note => `<li>${escapeHtml(note)}</li>`)
                    .join("");
        } else if (compliance) {
            notes.innerHTML =
                `<li>${escapeHtml(compliance)}</li>`;
        } else {
            notes.innerHTML =
                "<li>Content generated successfully.</li>";
        }
    }
}


/* =========================
   HTML ESCAPE
========================= */

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* =========================
   GENERATE
========================= */

async function generateCopy() {
    hideError();

    const productName =
        $("#productName")?.value.trim();

    const rawDescription =
        description?.value.trim();

    const platform =
        $("#platform")?.value;

    const tone =
        $("#tone")?.value;

    const temp =
        Number(temperature?.value || 0.7);

    const topPValue =
        Number(topP?.value || 0.9);

    if (!productName) {
        showError(
            "Please enter a product name."
        );
        return;
    }

    if (!rawDescription) {
        showError(
            "Please enter a product description."
        );
        return;
    }

    generateBtn.disabled = true;

    const originalText =
        generateBtn.textContent;

    generateBtn.textContent =
        "Generating...";

    try {
        const response =
            await fetch("/api/generate", {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    product_name: productName,
                    description: rawDescription,
                    platform: platform,
                    tone: tone,
                    temperature: temp,
                    top_p: topPValue
                })
            });

        const result =
            await response.json();

        if (!response.ok || !result.success) {
            throw new Error(
                result.error ||
                "Unable to generate copy."
            );
        }

        renderResult(result.data);

    } catch (error) {
        console.error(error);

        showError(
            error.message ||
            "Something went wrong while generating the copy."
        );

    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent =
            originalText;
    }
}


/* =========================
   FORM SUBMIT
========================= */

if (form) {
    form.addEventListener(
        "submit",
        function(event) {
            event.preventDefault();
            generateCopy();
        }
    );
}


/* =========================
   COPY TEXT
========================= */

async function copyText(text, button) {
    if (!text || text === "—") return;

    try {
        await navigator.clipboard.writeText(
            text
        );

        if (button) {
            const oldText =
                button.textContent;

            button.textContent =
                "Copied!";

            setTimeout(() => {
                button.textContent =
                    oldText;
            }, 1200);
        }

    } catch (error) {
        console.error(error);

        alert(
            "Copy failed. Please select and copy the text manually."
        );
    }
}


/* =========================
   INDIVIDUAL COPY BUTTONS
========================= */

document.addEventListener(
    "click",
    function(event) {

        const button =
            event.target.closest(
                "[data-copy-target]"
            );

        if (!button) return;

        const targetSelector =
            button.dataset.copyTarget;

        const target =
            document.querySelector(
                targetSelector
            );

        if (!target) return;

        copyText(
            target.textContent.trim(),
            button
        );
    }
);


/* =========================
   COPY ALL
========================= */

const copyAllButton =
    $("#copyAll");

if (copyAllButton) {

    copyAllButton.addEventListener(
        "click",
        function() {

            const sections = [];

            const subject =
                subjectValue?.textContent.trim();

            const headline =
                headlineValue?.textContent.trim();

            const body =
                bodyValue?.textContent.trim();

            const cta =
                ctaValue?.textContent.trim();

            const hashtags =
                hashtagsValue?.textContent.trim();

            if (subject && subject !== "—") {
                sections.push(
                    `SUBJECT\n${subject}`
                );
            }

            if (headline && headline !== "—") {
                sections.push(
                    `HEADLINE\n${headline}`
                );
            }

            if (body && body !== "—") {
                sections.push(
                    `BODY\n${body}`
                );
            }

            if (cta && cta !== "—") {
                sections.push(
                    `CALL TO ACTION\n${cta}`
                );
            }

            if (hashtags && hashtags !== "—") {
                sections.push(
                    `HASHTAGS\n${hashtags}`
                );
            }

            copyText(
                sections.join("\n\n"),
                copyAllButton
            );
        }
    );
}


/* =========================
   REGENERATE
========================= */

const regenerateButton =
    $("#regenerate");

if (regenerateButton) {

    regenerateButton.addEventListener(
        "click",
        function() {
            generateCopy();
        }
    );
}