// DOM Elements
const uploadImageBtn = document.getElementById("uploadImageBtn");
const uploadFormContainer = document.getElementById("uploadFormContainer");
const imageUploadForm = document.getElementById("imageUploadForm");
const cancelUploadBtn = document.getElementById("cancelUploadBtn");
const detectionCanvas = document.getElementById("detectionCanvas");
const detectionInfo = document.getElementById("detectionInfo");
const detectionSummary = document.getElementById("detectionSummary");
const detectionTimestamp = document.getElementById("detectionTimestamp");
const carCountElement = document.getElementById("carCount");
const truckCountElement = document.getElementById("truckCount");
const busCountElement = document.getElementById("busCount");
const motorcycleCountElement = document.getElementById("motorcycleCount");

// Set up event listeners
document.addEventListener("DOMContentLoaded", function () {
  // Show upload form when upload button is clicked
  uploadImageBtn.addEventListener("click", function () {
    detectionCanvas.style.display = "none";
    uploadFormContainer.classList.remove("d-none");
  });

  // Hide upload form when cancel button is clicked
  cancelUploadBtn.addEventListener("click", function () {
    uploadFormContainer.classList.add("d-none");
    detectionCanvas.style.display = "block";
  });

  // Handle image upload form submission
  imageUploadForm.addEventListener("submit", function (e) {
    e.preventDefault();

    const fileInput = document.getElementById("imageFile");
    const file = fileInput.files[0];

    if (!file) {
      alert("Please select an image file");
      return;
    }

    uploadAndDetectVehicles(file);
  });
});

// Upload image and detect vehicles
function uploadAndDetectVehicles(file) {
  // Show loading state
  uploadImageBtn.disabled = true;
  uploadImageBtn.innerHTML =
    '<i class="fas fa-spinner fa-spin me-1"></i> Processing...';

  const formData = new FormData();
  formData.append("file", file);

  // Send to API
  fetch(`${API_URL}/detect/`, {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      console.log("Detection results:", data);
      displayDetectionResults(data, file);

      // Hide upload form
      uploadFormContainer.classList.add("d-none");
      detectionCanvas.style.display = "block";

      // Update dashboard data
      updateVehicleCounts(data.detections);

      // Refresh traffic data table
      fetchTrafficData();
    })
    .catch((error) => {
      console.error("Error detecting vehicles:", error);
      alert("Error detecting vehicles. Please try again.");
    })
    .finally(() => {
      // Reset button state
      uploadImageBtn.disabled = false;
      uploadImageBtn.innerHTML =
        '<i class="fas fa-upload me-1"></i> Upload Image';
    });
}

// Example function to handle detection for a specific feed
function handleDetectionForFeed(feedNumber) {
  const canvas = document.getElementById(`detectionCanvas${feedNumber}`);
  const detectionInfo = document.getElementById(`detectionInfo${feedNumber}`);
  const detectionSummary = document.getElementById(
    `detectionSummary${feedNumber}`
  );

  // Simulate detection results (replace with actual detection logic)
  const mockDetections = [
    { class_name: "car", confidence: 0.95, bbox: [10, 10, 100, 100] },
    { class_name: "truck", confidence: 0.85, bbox: [200, 200, 300, 300] },
  ];

  // Display detection results
  detectionInfo.classList.remove("d-none");
  detectionSummary.textContent = `${mockDetections.length} vehicles detected`;

  // Draw detections on canvas (replace with actual drawing logic)
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  mockDetections.forEach((detection) => {
    const [x1, y1, x2, y2] = detection.bbox;
    ctx.strokeStyle = "red";
    ctx.lineWidth = 2;
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
  });
}

// Initialize detection for all feeds
document.addEventListener("DOMContentLoaded", function () {
  for (let i = 1; i <= 4; i++) {
    handleDetectionForFeed(i);
  }
});

function displayDetectionResults(data, imageFile) {
  // Create an image object
  const img = new Image();

  img.onload = function () {
    // Set canvas dimensions to match image
    const ctx = detectionCanvas.getContext("2d");
    detectionCanvas.width = img.width;
    detectionCanvas.height = img.height;

    // Draw the image
    ctx.drawImage(img, 0, 0);

    // Draw bounding boxes
    data.detections.forEach((detection) => {
      const [x1, y1, x2, y2] = detection.bbox;
      const width = x2 - x1;
      const height = y2 - y1;

      // Set style based on vehicle class
      ctx.lineWidth = 3;
      ctx.strokeStyle = getColorForClass(detection.class_name);

      // Draw rectangle
      ctx.strokeRect(x1, y1, width, height);

      // Draw label background
      ctx.fillStyle = getColorForClass(detection.class_name);
      const labelText = `${detection.class_name} ${Math.round(
        detection.confidence * 100
      )}%`;
      const labelWidth = ctx.measureText(labelText).width + 10;
      ctx.fillRect(x1, y1 - 25, labelWidth, 20);

      // Draw label text
      ctx.fillStyle = "white";
      ctx.font = "14px Arial";
      ctx.fillText(labelText, x1 + 5, y1 - 10);
    });

    // Show detection information
    detectionInfo.classList.remove("d-none");

    // Update timestamp
    const timestamp = new Date(data.timestamp).toLocaleString();
    detectionTimestamp.textContent = `Last detection: ${timestamp}`;
  };
}
