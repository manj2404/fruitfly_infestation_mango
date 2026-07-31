// ===============================
// Phenology Model Dashboard Script
// ===============================

// ===============================
// Site-wide Language Toggle
// ===============================
// The <html> element already gets the "lang-ta" class applied inline in
// base.html's <head> (before paint) if localStorage has a saved Tamil
// preference. This block wires up the dropdown UI and keeps everything
// (including the voice output) in sync with that same preference.

const SITE_LANGUAGE_KEY = "site_language";

function getSiteLanguage() {
    return document.documentElement.classList.contains("lang-ta") ? "ta" : "en";
}

function setSiteLanguage(lang) {
    document.documentElement.classList.toggle("lang-ta", lang === "ta");
    localStorage.setItem(SITE_LANGUAGE_KEY, lang);
    updateLangDropdownLabel(lang);
}

function updateLangDropdownLabel(lang) {
    const label = document.getElementById("langDropdownLabel");
    if (label) {
        label.textContent = lang === "ta" ? "தமிழ்" : "English";
    }
    document.querySelectorAll(".lang-dropdown-menu button").forEach(function (btn) {
        btn.classList.toggle("is-selected", btn.dataset.lang === lang);
    });
}

document.addEventListener("DOMContentLoaded", function () {
    const dropdownBtn = document.getElementById("langDropdownBtn");
    const dropdownMenu = document.getElementById("langDropdownMenu");

    updateLangDropdownLabel(getSiteLanguage());

    if (dropdownBtn && dropdownMenu) {
        dropdownBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            dropdownMenu.classList.toggle("open");
        });

        dropdownMenu.querySelectorAll("button[data-lang]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                setSiteLanguage(btn.dataset.lang);
                dropdownMenu.classList.remove("open");
                // If voice is currently speaking, restart so it matches the new language
                if ("speechSynthesis" in window && speechSynthesis.speaking) {
                    speechSynthesis.cancel();
                }
                // Keep the predicted-value display (e.g. HEALTHY vs ஆரோக்கியமானது) in sync
                const predictionText = document.getElementById("predictionText");
                if (predictionText) {
                    predictionText.textContent = btn.dataset.lang === "ta"
                        ? predictionText.dataset.ta
                        : predictionText.dataset.en;
                }
            });
        });

        document.addEventListener("click", function () {
            dropdownMenu.classList.remove("open");
        });
    }
});


// ===============================
// Dashboard Weather Widget
// ===============================
// Asks the browser for the farmer's location, then calls our own
// /api/weather endpoint (which in turn calls weather.py) to show
// today's temperature and place name at the top of the dashboard.

document.addEventListener("DOMContentLoaded", function () {
    const widget = document.getElementById("dashboardWeather");
    if (!widget) return; // not on the dashboard

    if (!("geolocation" in navigator)) return; // silently skip; not critical

    navigator.geolocation.getCurrentPosition(
        function (position) {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;

            fetch("/api/weather?latitude=" + lat + "&longitude=" + lon)
                .then(function (res) { return res.json(); })
                .then(function (data) {
                    if (data.error) return;
                    const tempEl = document.getElementById("dashboardWeatherTemp");
                    const locEl = document.getElementById("dashboardWeatherLoc");
                    if (tempEl) tempEl.textContent = data.temp_max + "°C / " + data.temp_min + "°C";
                    if (locEl) locEl.textContent = data.location_name;

                    // Also populate the small topbar chip on every page
                    const chip = document.getElementById("weatherInfo");
                    if (chip) {
                        chip.textContent = "🌡 " + data.temp_max + "°C / " + data.temp_min + "°C · 📍 " + data.location_name;
                        chip.style.display = "inline-block";
                    }

                    widget.style.display = "inline-flex";
                })
                .catch(function () { /* silently ignore — non-critical widget */ });
        },
        function () { /* location denied — silently skip the widget */ },
        { timeout: 8000 }
    );
});


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
    const voiceWarning = document.getElementById("voiceWarning");

    const data = panel.dataset;

    // ---- Voice list loading & caching ----
    // Chrome/Edge/Firefox load voices asynchronously. On first page load,
    // speechSynthesis.getVoices() often returns an empty array until the
    // "voiceschanged" event fires. We cache the list once it's ready so
    // Speak works correctly even on the very first click.
    let cachedVoices = [];

    function loadVoices() {
        return new Promise(function (resolve) {
            let voices = speechSynthesis.getVoices();
            if (voices.length > 0) {
                cachedVoices = voices;
                resolve(cachedVoices);
                return;
            }
            speechSynthesis.onvoiceschanged = function () {
                cachedVoices = speechSynthesis.getVoices();
                resolve(cachedVoices);
            };
            // Safety net: some browsers never fire onvoiceschanged
            setTimeout(function () {
                if (cachedVoices.length === 0) {
                    cachedVoices = speechSynthesis.getVoices();
                }
                resolve(cachedVoices);
            }, 1000);
        });
    }

    if ("speechSynthesis" in window) {
        loadVoices(); // start loading immediately, before the user clicks Speak
    }

    // Finds the best matching installed voice for a language prefix ("ta" or "en").
    // Tries an exact locale match first (e.g. "ta-IN"), then any voice whose
    // lang code starts with the prefix (e.g. "ta-LK"), then gives up gracefully.
    function findVoice(langPrefix) {
        const list = cachedVoices.length ? cachedVoices : speechSynthesis.getVoices();
        const exact = list.find(function (v) {
            return v.lang.toLowerCase() === langPrefix + "-in";
        });
        if (exact) return exact;

        const partial = list.find(function (v) {
            return v.lang.toLowerCase().startsWith(langPrefix);
        });
        return partial || null;
    }

    function showVoiceWarning(message) {
        if (!voiceWarning) return;
        voiceWarning.textContent = message;
        voiceWarning.style.display = "block";
    }

    function hideVoiceWarning() {
        if (!voiceWarning) return;
        voiceWarning.style.display = "none";
    }

    function buildEnglishSentence() {
        const status = data.prediction === "HEALTHY" ? "healthy" : "infected";

        return "Today's maximum temperature is " + data.tempMax + " degrees Celsius. " +
            "Minimum temperature is " + data.tempMin + " degrees Celsius. " +
            "The uploaded mango is " + status + ". " +
            "Confidence is " + data.confidence + " percent. " +
            "Fruit fly stage is " + data.stage + ". " +
            "Risk level is " + data.risk.toLowerCase() + ". " +
            "Recommendation: " + data.recommendation;
    }

    function buildTamilSentence() {
        return "இன்றைய அதிகபட்ச வெப்பநிலை " + data.tempMax + " டிகிரி செல்சியஸ். " +
            "குறைந்தபட்ச வெப்பநிலை " + data.tempMin + " டிகிரி செல்சியஸ். " +
            "பதிவேற்றப்பட்ட மாம்பழம் " + data.predictionTamil + ". " +
            "நம்பகத்தன்மை " + data.confidence + " சதவீதம். " +
            "பழ ஈ நிலை " + data.stageTamil + ". " +
            "ஆபத்து " + data.riskTamil + ". " +
            "பரிந்துரை: " + data.recommendationTamil;
    }

    function getSelectedLang() {
        return getSiteLanguage();
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
        hideVoiceWarning();

        const lang = getSelectedLang();
        const text = lang === "ta" ? buildTamilSentence() : buildEnglishSentence();
        const voice = findVoice(lang);

        if (lang === "ta" && !voice) {
            // No Tamil voice installed on this device/browser. Speaking will likely
            // be silent or garbled, so warn the user instead of failing silently.
            showVoiceWarning(
                "⚠️ No Tamil voice was found on this device. Install a Tamil voice " +
                "(Windows: Settings → Time & Language → Language & Region → Add Tamil) " +
                "and restart your browser, or switch to English."
            );
        }

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = lang === "ta" ? "ta-IN" : "en-IN";
        utterance.rate = 0.95;

        if (voice) {
            utterance.voice = voice;
        }

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
                maintainAspectRatio: false,
                cutout: "68%",
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }
});