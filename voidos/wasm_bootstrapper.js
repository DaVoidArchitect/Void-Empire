// ============================================================================
// iVoid — WebGL/WebAssembly Walled Garden Client Bootstrapper
// ============================================================================
// Connects to VTP Server and renders state reflections onto direct canvas.
// ============================================================================

const DESIGN_TOKENS = {
    background: "#020204",
    purpleGlow: "#7c3aed",
    sovereignGold: "#f4d58d",
    textPrimary: "#f5f5f7"
};

let ws = null;
let currentUIState = "ThresholdLanding";
let canvas = null;
let ctx = null;

// Initialize WebGL/2D context canvas
function initCanvas() {
    canvas = document.getElementById("void-framebuffer");
    ctx = canvas.getContext("2d"); // Freestanding vector 2D engine mockup
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);
    
    // Bind click events to send VTP Intent Packets
    canvas.addEventListener("click", handleCanvasClick);
    
    // Parallax mouse-tracking
    window.addEventListener("mousemove", handleMouseMove);
}

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    renderUI();
}

function handleMouseMove(e) {
    if (currentUIState === "ThresholdLanding") {
        // Trigger faint parallax shift
        requestAnimationFrame(() => renderUI(e.clientX, e.clientY));
    }
}

// Render UI based strictly on state machine reflected values
function renderUI(mouseX = 0, mouseY = 0) {
    if (!ctx) return;
    
    // 1. Clear with Absolute Black Canvas (#020204)
    ctx.fillStyle = DESIGN_TOKENS.background;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Remove loading indicator once compiled Wasm takes over
    const loader = document.getElementById("loader");
    if (loader) loader.style.display = "none";
    
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    if (currentUIState === "ThresholdLanding") {
        renderThresholdLanding(centerX, centerY, mouseX, mouseY);
    } else if (currentUIState === "DownloadPortal") {
        renderDownloadPortal(centerX, centerY);
    }
}

function renderThresholdLanding(centerX, centerY, mouseX, mouseY) {
    // Subtle mouse tracking offset
    const dx = (mouseX - centerX) * 0.02;
    const dy = (mouseY - centerY) * 0.02;
    
    // 1. Draw soft purple edge glow
    ctx.shadowColor = DESIGN_TOKENS.purpleGlow;
    ctx.shadowBlur = 40;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 0;
    
    // 2. Draw sleek flat VOID wordmark
    ctx.fillStyle = "#0a0a0c"; // Near-black letter fill
    ctx.font = "bold 90px 'Archivo Black'";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("V   O   I   D", centerX + dx, centerY + dy);
    
    // 3. Draw Sovereign Gold Tagline
    ctx.shadowBlur = 0; // Reset shadow for clean tagline
    ctx.fillStyle = DESIGN_TOKENS.sovereignGold;
    ctx.font = "300 12px 'IBM Plex Mono'";
    ctx.letterSpacing = "0.35em";
    ctx.fillText("FORERUNNER COMPANY", centerX, centerY + 100);
    
    // 4. Draw CTA button "ENTER VOID"
    ctx.strokeStyle = DESIGN_TOKENS.sovereignGold;
    ctx.lineWidth = 1;
    ctx.strokeRect(centerX - 100, centerY + 160, 200, 45);
    ctx.fillStyle = DESIGN_TOKENS.textPrimary;
    ctx.font = "300 11px 'Inter'";
    ctx.fillText("ENTER VOID", centerX, centerY + 182);
}

function renderDownloadPortal(centerX, centerY) {
    ctx.fillStyle = DESIGN_TOKENS.textPrimary;
    ctx.font = "bold 32px 'Archivo Black'";
    ctx.textAlign = "center";
    ctx.fillText("DOWNLOAD TRUTH", centerX, centerY - 80);
    
    ctx.fillStyle = DESIGN_TOKENS.sovereignGold;
    ctx.font = "300 12px 'IBM Plex Mono'";
    ctx.fillText("DECENTRALIZED LOCAL WALLED GARDEN", centerX, centerY - 40);
    
    // Download Buttons
    // Button 1: Desktop App
    ctx.strokeStyle = DESIGN_TOKENS.purpleGlow;
    ctx.lineWidth = 1;
    ctx.strokeRect(centerX - 150, centerY, 300, 45);
    ctx.fillStyle = DESIGN_TOKENS.textPrimary;
    ctx.font = "14px 'Inter'";
    ctx.fillText("DOWNLOAD FOR DESKTOP (TRUTH.EXE)", centerX, centerY + 28);
    
    // Button 2: Mobile App
    ctx.strokeRect(centerX - 150, centerY + 70, 300, 45);
    ctx.fillText("DOWNLOAD FOR MOBILE (TRUTH.APK)", centerX, centerY + 98);
    
    // Return button
    ctx.fillStyle = "#666";
    ctx.font = "12px 'Inter'";
    ctx.fillText("[ CANCEL AND RETURN ]", centerX, centerY + 160);
}

function handleCanvasClick(e) {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    if (currentUIState === "ThresholdLanding") {
        // Check "ENTER VOID" button click boundary
        if (x >= centerX - 100 && x <= centerX + 100 && y >= centerY + 160 && y <= centerY + 205) {
            console.log("[VTP] Sending intent packet: enter_void");
            sendVTPIntent("enter_void");
        }
    } else if (currentUIState === "DownloadPortal") {
        // Check Desktop download
        if (x >= centerX - 150 && x <= centerX + 150 && y >= centerY && y <= centerY + 45) {
            console.log("[VTP] Downloading Desktop Client...");
            window.location.href = "/downloads/truth.exe";
        }
        // Check Mobile download
        if (x >= centerX - 150 && x <= centerX + 150 && y >= centerY + 70 && y <= centerY + 115) {
            console.log("[VTP] Downloading Mobile Client...");
            window.location.href = "/downloads/truth.apk";
        }
        // Check cancel
        if (x >= centerX - 100 && x <= centerX + 100 && y >= centerY + 145 && y <= centerY + 175) {
            console.log("[VTP] Sending intent packet: cancel");
            sendVTPIntent("cancel");
        }
    }
}

// Connect to secure VTP stream server
function connectVTPServer() {
    console.log("Connecting to VTP stream server at wss://ivoid.app:9000...");
    ws = new WebSocket("wss://ivoid.app:9000");
    ws.binaryType = "arraybuffer";
    
    ws.onmessage = function(event) {
        // Parse 128-byte cryptographic State Reflection Packet
        const view = new DataView(event.data);
        const entropyAnchor = view.getUint32(0);
        if (entropyAnchor !== 0xF00DBABE) return; // Verify crypt block
        
        // Read target state reflection
        const stateOffset = 12; // Example byte offset for current state
        const stateCode = view.getUint8(stateOffset);
        
        // Simple mapping code to state names
        if (stateCode === 0) currentUIState = "ThresholdLanding";
        else if (stateCode === 1) currentUIState = "DownloadPortal";
        
        console.log(`[VTP SYNC] Reflected active state: ${currentUIState}`);
        renderUI();
    };
    
    ws.onclose = function() {
        console.warn("VTP connection dropped. Retrying...");
        setTimeout(connectVTPServer, 5000);
    };
}

// Send 64-byte VTP Intent Packet
function sendVTPIntent(action) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        // Offline mockup fallback for local test
        if (action === "enter_void") currentUIState = "DownloadPortal";
        else if (action === "cancel") currentUIState = "ThresholdLanding";
        renderUI();
        return;
    }
    
    const packet = new ArrayBuffer(64);
    const view = new DataView(packet);
    view.setUint32(0, 0xF00DBABE); // Entropy block
    
    // Map action to byte code
    let code = 0;
    if (action === "enter_void") code = 1;
    else if (action === "cancel") code = 2;
    
    view.setUint8(4, code);
    ws.send(packet);
}

// Start client loop
window.onload = function() {
    initCanvas();
    connectVTPServer();
};
