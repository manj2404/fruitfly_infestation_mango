// ===============================
// Phenology Model Dashboard Script
// ===============================

// Live Date & Time
function updateDateTime() {
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const date = now.toLocaleDateString('en-IN', options);
    const time = now.toLocaleTimeString();
    const element = document.getElementById("datetime");
    if (element) {
        element.innerHTML = "📅 " + date + " · 🕒 " + time;
    }
}
setInterval(updateDateTime, 1000);
updateDateTime();


// ===============================
// Sidebar toggle (mobile)
// ===============================

document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.getElementById("menuToggle");
    const sidebar = document.querySelector(".sidebar");

    if (toggle && sidebar) {
        toggle.addEventListener("click", function () {
            sidebar.classList.toggle("open");
        });

        document.addEventListener("click", function (e) {
            if (sidebar.classList.contains("open") &&
                !sidebar.contains(e.target) &&
                e.target !== toggle) {
                sidebar.classList.remove("open");
            }
        });
    }
});


// ===============================
// Voice Output (Bilingual: English / Tamil)
// ===============================

document.addEventListener("DOMContentLoaded", function () {
    const panel = document.getElementById("voicePanel");
    if (!panel) return; // not on the result page

    const speakBtn = document.getElementById("speakBtn");
    const stopBtn = document.getElementById("stopBtn");
    const langEn = document.getElementById("langEn");
    const langTa = document.getElementById("langTa");

    const data = panel.dataset;

    function buildEnglishSentence() {
        const status = data.prediction === "HEALTHY" ? "healthy" : "infected";

        return "The uploaded mango is " + status + ". " +
            "Confidence is " + data.confidence + " percent. " +
            "Fruit fly stage is " + data.stage + ". " +
            "Risk level is " + data.risk.toLowerCase() + ". " +
            "Recommendation: " + data.recommendation;
    }

    function buildTamilSentence() {
        return "பதிவேற்றப்பட்ட மாம்பழம் " + data.predictionTamil + ". " +
            "நம்பகத்தன்மை " + data.confidence + " சதவீதம். " +
            "பழ ஈ நிலை " + data.stageTamil + ". " +
            "ஆபத்து " + data.riskTamil + ". " +
            "பரிந்துரை: " + data.recommendationTamil;
    }

    function getSelectedLang() {
        return langTa && langTa.checked ? "ta" : "en";
    }

    function setSpeakingState(isSpeaking) {
        stopBtn.disabled = !isSpeaking;
        speakBtn.classList.toggle("is-speaking", isSpeaking);
        speakBtn.textContent = isSpeaking ? "🔊 Speaking..." : "🔊 Speak Result";
    }

    function speak() {
        if (!("speechSynthesis" in window)) {
            alert("Sorry, your browser does not support voice output.");
            return;
        }

        speechSynthesis.cancel(); // stop anything currently playing

        const lang = getSelectedLang();
        const text = lang === "ta" ? buildTamilSentence() : buildEnglishSentence();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = lang === "ta" ? "ta-IN" : "en-IN";
        utterance.rate = 0.95;

        utterance.onstart = function () { setSpeakingState(true); };
        utterance.onend = function () { setSpeakingState(false); };
        utterance.onerror = function () { setSpeakingState(false); };

        speechSynthesis.speak(utterance);
    }

    function stop() {
        speechSynthesis.cancel();
        setSpeakingState(false);
    }

    if (speakBtn) speakBtn.addEventListener("click", speak);
    if (stopBtn) stopBtn.addEventListener("click", stop);

    // If the user switches language while speaking, stop the current utterance
    [langEn, langTa].forEach(function (radio) {
        if (radio) {
            radio.addEventListener("change", function () {
                if (speechSynthesis.speaking) stop();
            });
        }
    });

    // Stop any speech if the user navigates away
    window.addEventListener("beforeunload", function () {
        speechSynthesis.cancel();
    });
});


// ===============================
// Confidence Chart
// ===============================

window.addEventListener("load", function () {
    const canvas = document.getElementById("confidenceChart");
    if (canvas) {
        let value = parseFloat(canvas.dataset.value);
        new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Confidence', 'Remaining'],
                datasets: [{
                    data: [value, 100 - value],
                    backgroundColor: ['#E8A33D', '#E8F5E9'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }
});
