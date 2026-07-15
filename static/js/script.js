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
// Voice Output (English)
// ===============================

function speakResult() {
    let prediction = document.getElementById("predictionText");
    if (prediction) {
        let msg = new SpeechSynthesisUtterance(prediction.innerText);
        msg.lang = "en-IN";
        speechSynthesis.speak(msg);
    }
}


// ===============================
// Tamil Voice
// ===============================

function speakTamil(text) {
    let msg = new SpeechSynthesisUtterance(text);
    msg.lang = "ta-IN";
    speechSynthesis.speak(msg);
}


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
