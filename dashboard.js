// Configuration
const API_URL = "http://localhost:8000"; // Change to your FastAPI backend URL

// Global variables
let trafficData = [];
let activeSection = "dashboard";

// DOM Elements
const navLinks = document.querySelectorAll(".nav-link");
const totalVehicleCountElement = document.getElementById("totalVehicleCount");
const trafficFlowStatusElement = document.getElementById("trafficFlowStatus");
const activeSignalsCountElement = document.getElementById("activeSignalsCount");
const emergencyCountElement = document.getElementById("emergencyCount");
const trafficDataTableElement = document.getElementById("trafficDataTable");
const refreshTableBtn = document.getElementById("refreshTableBtn");

// WebSocket connection for real-time updates
let socket;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

// Initialize the dashboard
document.addEventListener("DOMContentLoaded", function () {
  console.log("Dashboard initialized");

  // Set up navigation
  setupNavigation();

  // Fetch initial data
  fetchDashboardData();
  fetchTrafficData();

  // Set up event listeners
  refreshTableBtn.addEventListener("click", fetchTrafficData);

  // Simulate real-time updates
  setInterval(updateDashboardData, 10000); // Update every 10 seconds

  // Initialize WebSocket connection
  connectWebSocket();
});

// Set up navigation between sections
function setupNavigation() {
  navLinks.forEach((link) => {
    link.addEventListener("click", function (e) {
      e.preventDefault();

      // Remove active class from all links
      navLinks.forEach((l) => l.classList.remove("active"));

      // Add active class to clicked link
      this.classList.add("active");

      // Get the section id from the link id
      const sectionId = this.id.replace("Link", "");

      // Update active section
      activeSection = sectionId;
      console.log(`Switched to ${sectionId} section`);

      // You can extend this to show/hide different sections
      // based on the active section
    });
  });
}

// Fetch dashboard summary data
function fetchDashboardData() {
  // In a real application, you would fetch this data from your API
  // For now, we'll use mock data

  // Simulate API call
  setTimeout(() => {
    // Mock data
    const data = {
      totalVehicles: 1247,
      trafficFlow: "Moderate",
      activeSignals: 4,
      emergencyVehicles: 0,
    };

    // Update dashboard
    updateDashboardUI(data);
  }, 500);
}

// Update dashboard UI with data
function updateDashboardUI(data) {
  totalVehicleCountElement.textContent = data.totalVehicles;
  trafficFlowStatusElement.textContent = data.trafficFlow;
  activeSignalsCountElement.textContent = data.activeSignals;
  emergencyCountElement.textContent = data.emergencyVehicles;

  // Update traffic flow status color
  if (data.trafficFlow === "Heavy") {
    trafficFlowStatusElement.parentElement.parentElement.classList.remove(
      "bg-success"
    );
    trafficFlowStatusElement.parentElement.parentElement.classList.add(
      "bg-danger"
    );
  } else if (data.trafficFlow === "Moderate") {
    trafficFlowStatusElement.parentElement.parentElement.classList.remove(
      "bg-success",
      "bg-danger"
    );
    trafficFlowStatusElement.parentElement.parentElement.classList.add(
      "bg-warning"
    );
  } else {
    trafficFlowStatusElement.parentElement.parentElement.classList.remove(
      "bg-warning",
      "bg-danger"
    );
    trafficFlowStatusElement.parentElement.parentElement.classList.add(
      "bg-success"
    );
  }

  // Update emergency status
  if (data.emergencyVehicles > 0) {
    document.getElementById("emergencyAlert").classList.remove("d-none");
  } else {
    document.getElementById("emergencyAlert").classList.add("d-none");
  }
}

// Fetch traffic data for the table
function fetchTrafficData() {
  console.log("Fetching traffic data...");

  // Show loading state
  trafficDataTableElement.innerHTML =
    '<tr><td colspan="5" class="text-center">Loading data...</td></tr>';

  // Fetch data from API
  fetch(`${API_URL}/traffic-data/`)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      console.log("Traffic data received:", data);
      trafficData = data.traffic_data || [];
      renderTrafficDataTable();
    })
    .catch((error) => {
      console.error("Error fetching traffic data:", error);
      trafficDataTableElement.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-danger">
                        Error loading data. Please try again.
                        <button class="btn btn-sm btn-link" onclick="fetchTrafficData()">Retry</button>
                    </td>
                </tr>
            `;
    });
}

// Render traffic data table
function renderTrafficDataTable() {
  if (trafficData.length === 0) {
    trafficDataTableElement.innerHTML =
      '<tr><td colspan="5" class="text-center">No traffic data available</td></tr>';
    return;
  }

  let tableHtml = "";

  trafficData.forEach((record) => {
    const data = record.data;
    const timestamp = new Date(data.timestamp).toLocaleString();
    const vehicleCount = data.detections ? data.detections.length : 0;

    let status = "Normal";
    let statusClass = "success";

    if (vehicleCount > 20) {
      status = "Heavy";
      statusClass = "danger";
    } else if (vehicleCount > 10) {
      status = "Moderate";
      statusClass = "warning";
    }

    tableHtml += `
            <tr>
                <td>${record.id}</td>
                <td>${timestamp}</td>
                <td>${vehicleCount}</td>
                <td><span class="badge bg-${statusClass}">${status}</span></td>
                <td>
                    <button class="btn btn-sm btn-primary view-details-btn" data-id="${record.id}">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            </tr>
        `;
  });

  trafficDataTableElement.innerHTML = tableHtml;

  // Add event listeners to view buttons
  document.querySelectorAll(".view-details-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const recordId = this.getAttribute("data-id");
      viewTrafficDetails(recordId);
    });
  });
}

// View traffic details
function viewTrafficDetails(recordId) {
  const record = trafficData.find((r) => r.id == recordId);

  if (!record) {
    alert("Record not found");
    return;
  }

  // You could implement a modal to show details or navigate to a details page
  alert(
    `Details for Record ID ${recordId}:\n\n${JSON.stringify(
      record.data,
      null,
      2
    )}`
  );
}

// Simulate real-time updates
function updateDashboardData() {
  if (activeSection !== "dashboard") return;

  // Simulate changing data
  const currentVehicles = parseInt(totalVehicleCountElement.textContent);
  const vehicleChange = Math.floor(Math.random() * 30) - 10; // Random change between -10 and 20
  const newVehicleCount = Math.max(0, currentVehicles + vehicleChange);

  const flowOptions = ["Light", "Moderate", "Heavy"];
  const randomFlow =
    flowOptions[Math.floor(Math.random() * flowOptions.length)];

  const newEmergencyCount = Math.random() < 0.1 ? 1 : 0; // 10% chance of emergency

  updateDashboardUI({
    totalVehicles: newVehicleCount,
    trafficFlow: randomFlow,
    activeSignals: 4,
    emergencyVehicles: newEmergencyCount,
  });
}

// Upload image for detection
function uploadAndDetectVehicles(file) {
  const formData = new FormData();
  formData.append("file", file);

  fetch(`${API_URL}/detect/`, {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      console.log("Detection results:", data);
      // Display results
    })
    .catch((error) => {
      console.error("Error detecting vehicles:", error);
    });
}

// WebSocket connection for real-time updates
function connectWebSocket() {
  socket = new WebSocket(`ws://${window.location.host}/ws`);

  socket.onopen = function (e) {
    console.log("Connected to server");
    reconnectAttempts = 0;
  };

  socket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    updateDashboard(data.traffic_data);
    updateDetection(data.detection_data);
  };

  socket.onclose = function (event) {
    console.log("Connection closed");
    // Try to reconnect if not max attempts reached
    if (reconnectAttempts < maxReconnectAttempts) {
      reconnectAttempts++;
      setTimeout(connectWebSocket, 3000); // Wait 3 seconds before reconnecting
    }
  };

  socket.onerror = function (error) {
    console.log(`WebSocket error: ${error}`);
  };
}

// Update dashboard with new traffic data
function updateDashboard(data) {
  // Update metrics
  document.getElementById("totalVehicleCount").textContent =
    data.total_vehicles_today;
  document.getElementById("trafficFlowStatus").textContent =
    data.congestion_level === "HIGH" ? "Congested" : "Normal";
  document.getElementById("activeSignalsCount").textContent =
    data.active_signals;
  document.getElementById("emergencyCount").textContent =
    data.emergency_vehicles;

  // Update traffic light display
  updateTrafficLight(data.current_phase);

  // Update signal timings
  document.getElementById("nsGreenTime").textContent = data.ns_green_time + "s";
  document.getElementById("ewGreenTime").textContent = data.ew_green_time + "s";

  // Set progress bars based on current values
  const nsPercentage = (data.ns_green_time / 60) * 100;
  const ewPercentage = (data.ew_green_time / 60) * 100;
  document.getElementById("nsProgressBar").style.width = `${nsPercentage}%`;
  document.getElementById("ewProgressBar").style.width = `${ewPercentage}%`;

  // If traffic flow status changes, update coloring
  if (data.congestion_level === "HIGH") {
    document
      .getElementById("trafficFlowStatus")
      .closest(".card")
      .classList.remove("bg-success");
    document
      .getElementById("trafficFlowStatus")
      .closest(".card")
      .classList.add("bg-danger");
  } else {
    document
      .getElementById("trafficFlowStatus")
      .closest(".card")
      .classList.remove("bg-danger");
    document
      .getElementById("trafficFlowStatus")
      .closest(".card")
      .classList.add("bg-success");
  }
}

// Update traffic light visualization
function updateTrafficLight(phase) {
  const redLight = document.getElementById("redLight");
  const yellowLight = document.getElementById("yellowLight");
  const greenLight = document.getElementById("greenLight");

  // Reset all lights
  redLight.classList.remove("active");
  yellowLight.classList.remove("active");
  greenLight.classList.remove("active");

  // Activate the current phase light
  if (phase === "RED") {
    redLight.classList.add("active");
    document.getElementById("currentPhase").textContent = "STOP (RED)";
  } else if (phase === "YELLOW") {
    yellowLight.classList.add("active");
    document.getElementById("currentPhase").textContent = "CAUTION (YELLOW)";
  } else {
    greenLight.classList.add("active");
    document.getElementById("currentPhase").textContent = "GO (GREEN)";
  }
}

// Update detection displays
function updateDetection(data) {
  for (let i = 1; i <= 4; i++) {
    if (data[i] && data[i].vehicles > 0) {
      document.getElementById(`detectionInfo${i}`).classList.remove("d-none");
      document.getElementById(`detectionSummary${i}`).textContent =
        data[i].summary;
    }
  }

  // Update the detection timestamp if any camera has data
  if (data["1"].timestamp) {
    document.getElementById(
      "detectionTimestamp"
    ).textContent = `Last updated: ${data["1"].timestamp}`;
  }
}

// Add event listeners for buttons
document.addEventListener("DOMContentLoaded", function () {
  // Handle optimize signals button
  document
    .getElementById("optimizeSignalsBtn")
    .addEventListener("click", function () {
      // Add loading indicator
      this.innerHTML =
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Optimizing...';
      this.disabled = true;

      // Simulate optimization (in real app, would call API)
      setTimeout(() => {
        this.innerHTML = '<i class="fas fa-sync me-1"></i> Optimize Signals';
        this.disabled = false;
        alert("Signal optimization complete!");
      }, 2000);
    });

  // Handle emergency simulation button
  document
    .getElementById("simulateEmergencyBtn")
    .addEventListener("click", function () {
      const emergencyAlert = document.getElementById("emergencyAlert");
      emergencyAlert.classList.toggle("d-none");

      if (!emergencyAlert.classList.contains("d-none")) {
        // Simulate emergency route change
        document.getElementById("emergencyRoute").textContent =
          "Route: East-West";
      }
    });

  // Handle table refresh button
  document
    .getElementById("refreshTableBtn")
    .addEventListener("click", function () {
      // Add loading indicator
      this.innerHTML =
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...';
      this.disabled = true;

      // Simulate loading new data (in real app, would fetch from API)
      setTimeout(() => {
        this.innerHTML = '<i class="fas fa-sync me-1"></i> Refresh';
        this.disabled = false;

        // Update table with demo data
        const tableBody = document.getElementById("trafficDataTable");
        tableBody.innerHTML = `
                <tr>
                    <td>1</td>
                    <td>${new Date().toLocaleString()}</td>
                    <td>${
                      document.getElementById("totalVehicleCount").textContent
                    }</td>
                    <td><span class="badge bg-success">Normal</span></td>
                    <td><button class="btn btn-sm btn-outline-info">View Details</button></td>
                </tr>
            `;
      }, 1000);
    });
});
