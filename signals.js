function initializeTrafficSignal() {
  updateTrafficSignal(signalPhases.GREEN);
}

const signalPhases = {
  GREEN: "GREEN",
  YELLOW: "YELLOW",
  RED: "RED",
};

let currentPhase = signalPhases.GREEN;
let nsGreenTime = 30; // North-South green light duration
let ewGreenTime = 20; // East-West green light duration

function updateTrafficSignal(phase) {
  console.log(`Updating traffic signal to: ${phase}`);

  currentPhase = phase;
  document.getElementById("currentPhase").textContent = currentPhase;

  // Update traffic light visualization
  document
    .getElementById("redLight")
    .classList.toggle("active", currentPhase === signalPhases.RED);
  document
    .getElementById("yellowLight")
    .classList.toggle("active", currentPhase === signalPhases.YELLOW);
  document
    .getElementById("greenLight")
    .classList.toggle("active", currentPhase === signalPhases.GREEN);
}

function optimizeSignals() {
  // Logic to optimize signals based on traffic data
  // This is a placeholder for the actual optimization logic
  console.log("Optimizing signals...");
  // Simulate optimization
  setTimeout(() => {
    nsGreenTime = Math.random() * 60; // Randomize green time for demonstration
    ewGreenTime = Math.random() * 60; // Randomize green time for demonstration
    updateTrafficSignal(signalPhases.GREEN);
    console.log("Signals optimized!");
  }, 2000);
}

document.addEventListener("DOMContentLoaded", initializeTrafficSignal);
// Event listeners for buttons

document
  .getElementById("optimizeSignalsBtn")
  .addEventListener("click", optimizeSignals);

// Simulate traffic signal changes
setInterval(() => {
  if (currentPhase === signalPhases.GREEN) {
    updateTrafficSignal(signalPhases.YELLOW);
    setTimeout(() => updateTrafficSignal(signalPhases.RED), 5000);
  } else if (currentPhase === signalPhases.RED) {
    updateTrafficSignal(signalPhases.GREEN);
  }
}, nsGreenTime * 1000);
