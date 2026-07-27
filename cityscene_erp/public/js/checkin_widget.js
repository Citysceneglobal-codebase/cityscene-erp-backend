// =============================================================
// Employee Check-In / Check-Out Widget — cityscene_erp v17
//
// HOW TO USE:
//   1. In the Frappe Desk, open the Workspace you want (e.g. HR)
//   2. Click "Edit" → "+" → "Custom HTML"
//   3. Paste the HTML block (see checkin_widget_html_block.html)
//   4. In the same block's "Script" section (or as a Client Script
//      of type "Page"), paste this entire JS file content.
// =============================================================

// ── Guard: only run when the widget HTML is present ────────────
const customBlock = root_element.querySelector(".checkin-widget-wrapper");
if (!customBlock) return;

const checkButton       = customBlock.querySelector("#cscCheckButton");
const checkTimerDisplay = customBlock.querySelector("#cscTimerDisplay");

// ── State ───────────────────────────────────────────────────────
let employeeId        = null;
let employeeShift     = null;
let capturedImageB64  = null;
let isCheckedIn       = false;
let isFetchingLoc     = false;
let isProcessing      = false;
let currentFacingMode = "user";

// ── Timer Manager ───────────────────────────────────────────────
const TimerManager = {
  startTime:   null,
  accumulated: 0,
  interval:    null,

  start() {
    if (this.startTime) return;
    this.startTime = moment();
    this.interval  = setInterval(() => this._render(), 1000);
  },

  stop() {
    if (!this.startTime) return;
    this.accumulated += moment().diff(this.startTime, "seconds");
    clearInterval(this.interval);
    this.startTime = null;
    this._render();
  },

  reset() {
    clearInterval(this.interval);
    this.startTime   = null;
    this.accumulated = 0;
    this._render();
  },

  _render() {
    const total = this.accumulated +
      (this.startTime ? moment().diff(this.startTime, "seconds") : 0);
    if (checkTimerDisplay) {
      checkTimerDisplay.textContent = moment.utc(total * 1000).format("HH:mm:ss");
    }
  },
};

// ── Button toggle helper ────────────────────────────────────────
function setButtonState(checkedIn) {
  if (!checkButton) return;
  checkButton.textContent = checkedIn ? "Check Out" : "Check In";
  checkButton.classList.toggle("btn-check-out", checkedIn);
  checkButton.classList.toggle("btn-check",     !checkedIn);
}

// ── Upload Selfie ───────────────────────────────────────────────
async function uploadSelfie(checkinName, base64Str) {
  try {
    const res = await fetch(`data:image/jpeg;base64,${base64Str}`);
    const blob = await res.blob();
    
    let formData = new FormData();
    formData.append("file", blob, `selfie_${checkinName}.jpg`);
    formData.append("is_private", 0);
    formData.append("folder", "Home");
    formData.append("doctype", "Employee Checkin");
    formData.append("docname", checkinName);
    
    const response = await fetch('/api/method/upload_file', {
        method: 'POST',
        headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token },
        body: formData
    });
    
    const result = await response.json();
    if (result.message && result.message.file_url) {
      // Update the custom_selfie field on the document!
      await frappe.db.set_value('Employee Checkin', checkinName, 'custom_selfie', result.message.file_url);
      return result.message.file_url;
    }
  } catch (err) {
    console.error("Selfie upload error:", err);
    throw err;
  }
}

// ── Fetch employee linked to the current user ───────────────────
function fetchEmployee() {
  return new Promise((resolve, reject) => {
    frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "Employee",
        filters: { user_id: frappe.session.user },
        fields: ["name", "default_shift"],
      },
      callback({ message }) {
        if (message && message.length) {
          employeeId    = message[0].name;
          employeeShift = message[0].default_shift;
          resolve();
        } else {
          reject("No employee record found for this user.");
        }
      },
      error: (err) => reject(err),
    });
  });
}

// ── Restore today's timer state from server ─────────────────────
function fetchInitialState() {
  frappe.call({
    method: "cityscene_erp.api.checkin_utils.calculate_employee_daily_timings",
    args: { employee_id: employeeId },
    callback({ message }) {
      if (!message) return;
      const { total_seconds = 0, last_action = "" } = message;

      TimerManager.accumulated = total_seconds;
      isCheckedIn = last_action === "IN";

      if (isCheckedIn) TimerManager.start();

      setButtonState(isCheckedIn);
      TimerManager._render();
    },
  });
}

// ── Upload selfie attachment ────────────────────────────────────
async function uploadSelfie(docname, base64) {
  const loader = document.createElement("div");
  loader.id = "cscUploadIndicator";
  document.body.appendChild(loader);

  try {
    await frappe.call({
      method: "cityscene_erp.api.checkin_utils.upload_selfie",
      args: {
        base64_content: base64,
        filename: `checkin_${isCheckedIn ? "OUT" : "IN"}_${employeeId}_${Date.now()}.jpg`,
        doctype: "Employee Checkin",
        docname: docname,
        is_private: 1,
      },
      freeze: false,
    });
  } finally {
    const el = document.getElementById("cscUploadIndicator");
    if (el) el.remove();
  }
}

// ── Camera capture ──────────────────────────────────────────────
function handleImageCapture() {
  return new Promise(async (resolve, reject) => {
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: currentFacingMode },
        audio: false,
      });
    } catch (err) {
      return reject("Camera access failed: " + err.message);
    }

    // Video element
    const video = document.createElement("video");
    video.setAttribute("autoplay", "");
    video.setAttribute("playsinline", "");
    Object.assign(video.style, {
      position:  "fixed",
      top:       "50%",
      left:      "50%",
      transform: currentFacingMode === "user"
        ? "translate(-50%, -50%) scaleX(-1)"
        : "translate(-50%, -50%)",
      zIndex:    "9999",
      maxWidth:  "90vw",
      maxHeight: "60vh",
      borderRadius: "8px",
      boxShadow: "0 8px 40px rgba(0,0,0,0.6)",
    });
    document.body.appendChild(video);
    video.srcObject = stream;
    await video.play();
    await new Promise((r) => setTimeout(r, 500)); // warm-up

    // Dark overlay
    const overlay = document.createElement("div");
    Object.assign(overlay.style, {
      position: "fixed", inset: "0",
      background: "rgba(0,0,0,0.75)",
      zIndex: "9998",
    });
    document.body.appendChild(overlay);

    // Capture button
    const captureBtn = document.createElement("button");
    captureBtn.className = "csc-cam-btn csc-cam-capture";
    captureBtn.innerText = "📸 Capture";
    document.body.appendChild(captureBtn);

    // Switch camera button
    const switchBtn = document.createElement("button");
    switchBtn.className = "csc-cam-btn csc-cam-switch";
    switchBtn.innerText = "🔄 Switch Camera";
    document.body.appendChild(switchBtn);

    // Close button
    const closeBtn = document.createElement("button");
    closeBtn.className = "csc-cam-btn csc-cam-close";
    closeBtn.innerText = "✕";
    document.body.appendChild(closeBtn);

    const cleanup = () => {
      stream.getTracks().forEach((t) => t.stop());
      [video, overlay, captureBtn, switchBtn, closeBtn].forEach((el) => el.remove());
    };

    // Switch camera
    switchBtn.onclick = async () => {
      cleanup();
      currentFacingMode = currentFacingMode === "user" ? "environment" : "user";
      try {
        resolve(await handleImageCapture());
      } catch (e) {
        reject(e);
      }
    };

    // Close / cancel
    closeBtn.onclick = () => {
      cleanup();
      resolve(null); // null = cancelled
    };

    // Capture
    captureBtn.onclick = () => {
      const canvas = document.createElement("canvas");
      canvas.width  = 480;
      canvas.height = 360;
      const ctx = canvas.getContext("2d");

      if (currentFacingMode === "user") {
        ctx.translate(canvas.width, 0);
        ctx.scale(-1, 1);
      }
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      capturedImageB64 = canvas.toDataURL("image/jpeg", 0.7).split(",")[1];

      // Show preview
      const preview = customBlock.querySelector("#cscPhotoPreview");
      if (preview) {
        preview.src = `data:image/jpeg;base64,${capturedImageB64}`;
        preview.style.display = "block";
      }

      cleanup();
      resolve(capturedImageB64);
    };
  });
}

// ── Geolocation + Checkin insert ────────────────────────────────
function doCheckin() {
  return new Promise((resolve) => {
    if (isFetchingLoc) return resolve(false);
    isFetchingLoc = true;

    const logType = isCheckedIn ? "OUT" : "IN";

    const onError = (msg) => {
      isFetchingLoc = false;
      frappe.msgprint(msg);
      resolve(false);
    };

    const locTimeout = setTimeout(() => onError("Location timed out. Please try again."), 12000);

    const tryGeo = () => {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          clearTimeout(locTimeout);
          isFetchingLoc = false;

          try {
            const res = await frappe.call({
              method: "frappe.client.insert",
              args: {
                doc: {
                  doctype:             "Employee Checkin",
                  employee:            employeeId,
                  log_type:            logType,
                  time:                frappe.datetime.now_datetime(),
                  skip_auto_attendance: 0,
                  latitude:            position.coords.latitude,
                  longitude:           position.coords.longitude,
                  geolocation: JSON.stringify({
                    type: "FeatureCollection",
                    features: [{
                      type: "Feature",
                      properties: {},
                      geometry: {
                        type: "Point",
                        coordinates: [position.coords.longitude, position.coords.latitude]
                      }
                    }]
                  }),
                  shift:               employeeShift || undefined,
                },
              },
              freeze: true,
            });

            const checkinName = res.message?.name;

            // Upload selfie (non-blocking on failure)
            if (checkinName && capturedImageB64) {
              try {
                await uploadSelfie(checkinName, capturedImageB64);
              } catch (_) {
                frappe.show_alert({ message: "Selfie upload failed (checkin recorded).", indicator: "orange" }, 5);
              }
            }

            // Update timer & button
            if (logType === "IN") {
              isCheckedIn = true;
              TimerManager.start();
            } else {
              isCheckedIn = false;
              TimerManager.stop();
            }
            setButtonState(isCheckedIn);

            resolve(true);
          } catch (err) {
            console.error("Checkin insert failed", err);
            frappe.msgprint("Could not save check-in/out record. Please try again.");
            resolve(false);
          }
        },
        (err) => {
          clearTimeout(locTimeout);
          isFetchingLoc = false;
          if (err.code === 1) {
            frappe.msgprint("Location access denied. Please allow location in your browser settings.");
          } else {
            frappe.msgprint("Location error: " + err.message);
          }
          resolve(false);
        },
        { timeout: 11000, enableHighAccuracy: true }
      );
    };

    if (navigator.permissions) {
      navigator.permissions.query({ name: "geolocation" }).then((result) => {
        if (result.state === "granted" || result.state === "prompt") {
          tryGeo();
        } else {
          isFetchingLoc = false;
          frappe.show_alert({ message: "Location permission denied. Please enable and try again.", indicator: "red" }, 4);
          resolve(false);
        }
      });
    } else {
      tryGeo();
    }
  });
}

// ── Main click handler ──────────────────────────────────────────
async function handleCheckClick() {
  if (isProcessing) return;
  isProcessing = true;
  checkButton.disabled = true;

  if (!navigator.geolocation) {
    frappe.msgprint("Geolocation is not supported by your browser.");
    isProcessing = false;
    checkButton.disabled = false;
    return;
  }

  try {
    // Step 1: capture selfie
    const captured = await handleImageCapture();

    if (!captured) {
      // User cancelled camera
      frappe.show_alert({ message: "Selfie cancelled. Check-in not recorded.", indicator: "orange" }, 4);
      isProcessing = false;
      checkButton.disabled = false;
      return;
    }

    // Step 2: get location & insert record
    const success = await doCheckin();

    if (success) {
      const action = isCheckedIn ? "In" : "Out";
      frappe.show_alert({ message: `Check-${action} recorded successfully ✓`, indicator: "green" }, 5);
    } else {
      frappe.show_alert({ message: "Check-in/out failed. Please try again.", indicator: "red" }, 5);
    }
  } catch (e) {
    console.error("Check handler error:", e);
    frappe.show_alert({ message: "Unexpected error: " + e, indicator: "red" }, 5);
  }

  isProcessing = false;
  checkButton.disabled = false;
}

// ── Boot ────────────────────────────────────────────────────────
fetchEmployee()
  .then(() => {
    fetchInitialState();
    checkButton.addEventListener("click", handleCheckClick);
  })
  .catch((err) => {
    console.warn("Employee not found:", err);
    if (checkButton) {
      checkButton.disabled = true;
      checkButton.title = "No employee record linked to your user.";
    }
  });
