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

let mouseX = 0;
let mouseY = 0;
let rotationAngle = 0;
let lastTime = 0;

// Preload portal icon
const portalImg = new Image();
portalImg.src = "void_portal_icon.png";
portalImg.onload = () => {
    if (ctx) renderUI();
};

// Generate background stars
const stars = [];
for (let i = 0; i < 40; i++) {
    stars.push({
        x: Math.random(),
        y: Math.random(),
        size: Math.random() * 1.2 + 0.4,
        phase: Math.random() * Math.PI * 2,
        speed: Math.random() * 0.02 + 0.005
    });
}

// Initialize WebGL/2D context canvas
function initCanvas() {
    canvas = document.getElementById("void-framebuffer");
    ctx = canvas.getContext("2d");
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);
    
    // Bind click events to send VTP Intent Packets
    canvas.addEventListener("click", handleCanvasClick);
    
    // Mouse tracking
    window.addEventListener("mousemove", handleMouseMove);
}

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    renderUI();
}

function handleMouseMove(e) {
    const rect = canvas.getBoundingClientRect();
    mouseX = e.clientX - rect.left;
    mouseY = e.clientY - rect.top;
}

// Main animation loop
function animationLoop(timestamp) {
    if (!lastTime) lastTime = timestamp;
    const elapsed = timestamp - lastTime;
    lastTime = timestamp;
    
    // Rotate galaxy slowly
    rotationAngle += (elapsed * 0.0004); // 0.0004 radians per ms
    
    renderUI();
    requestAnimationFrame(animationLoop);
}

// Draw four-point star
function drawFourPointStar(ctx, cx, cy, outerRadius, innerRadius, color = "#ffffff") {
    ctx.save();
    ctx.beginPath();
    let rot = Math.PI / 2 * 3;
    let step = Math.PI / 4;
    
    ctx.moveTo(cx, cy - outerRadius);
    for (let i = 0; i < 4; i++) {
        let x = cx + Math.cos(rot) * outerRadius;
        let y = cy + Math.sin(rot) * outerRadius;
        ctx.lineTo(x, y);
        rot += step;
        
        x = cx + Math.cos(rot) * innerRadius;
        y = cy + Math.sin(rot) * innerRadius;
        ctx.lineTo(x, y);
        rot += step;
    }
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.shadowColor = color;
    ctx.shadowBlur = 10;
    ctx.fill();
    ctx.restore();
}

function drawBackgroundStars(ctx, width, height) {
    ctx.save();
    for (const star of stars) {
        star.phase += star.speed;
        const opacity = 0.1 + Math.sin(star.phase) * 0.08;
        ctx.fillStyle = `rgba(255, 255, 255, ${opacity})`;
        ctx.beginPath();
        ctx.arc(star.x * width, star.y * height, star.size, 0, Math.PI * 2);
        ctx.fill();
    }
    ctx.restore();
}

// Geometric Letter Drawing
function drawV(ctx, x, y) {
    ctx.beginPath();
    ctx.moveTo(x - 45, y - 65);
    ctx.lineTo(x, y + 65);
    ctx.lineTo(x + 45, y - 65);
    strokeLetter(ctx);
}

function drawI(ctx, x, y) {
    ctx.beginPath();
    ctx.moveTo(x, y - 65);
    ctx.lineTo(x, y + 65);
    strokeLetter(ctx);
}

function drawD(ctx, x, y) {
    ctx.beginPath();
    ctx.moveTo(x - 35, y + 65);
    ctx.lineTo(x - 35, y - 65);
    ctx.arc(x - 35, y, 65, -Math.PI / 2, Math.PI / 2);
    ctx.lineTo(x - 35, y + 65);
    strokeLetter(ctx);
}

function strokeLetter(ctx) {
    ctx.save();
    // 1. Purple outer glow rim
    ctx.shadowColor = "rgba(124, 58, 237, 0.9)";
    ctx.shadowBlur = 25;
    ctx.strokeStyle = "rgba(124, 58, 237, 0.4)";
    ctx.lineWidth = 4;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.stroke();
    
    // 2. Crisp inner hairline stroke
    ctx.shadowBlur = 0;
    ctx.strokeStyle = "#e9d5ff";
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.restore();
}

// Render UI based strictly on state machine reflected values
function renderUI() {
    if (!ctx) return;
    
    // 1. Clear with Absolute Black Canvas
    ctx.fillStyle = DESIGN_TOKENS.background;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // 2. Draw pulsing background stars
    drawBackgroundStars(ctx, canvas.width, canvas.height);
    
    // Remove loading indicator once compiled Wasm takes over
    const loader = document.getElementById("loader");
    if (loader) loader.style.display = "none";
    
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    let cursor = "default";
    
    if (currentUIState === "ThresholdLanding") {
        cursor = renderThresholdLanding(centerX, centerY);
    } else if (currentUIState === "DownloadPortal") {
        cursor = renderDownloadPortal(centerX, centerY);
    }
    
    document.body.style.cursor = cursor;
}

function renderThresholdLanding(centerX, centerY) {
    // Subtle mouse tracking offset
    const dx = (mouseX - centerX) * 0.015;
    const dy = (mouseY - centerY) * 0.015;
    
    // Render letters V, O, I, D with exact spacing
    // V
    drawV(ctx, centerX - 220 + dx, centerY + dy);
    
    // O (Rotated Portal Icon)
    ctx.save();
    ctx.translate(centerX - 70 + dx, centerY + dy);
    ctx.rotate(rotationAngle);
    if (portalImg.complete) {
        ctx.shadowColor = "rgba(124, 58, 237, 0.6)";
        ctx.shadowBlur = 30;
        ctx.drawImage(portalImg, -70, -70, 140, 140);
    } else {
        // Fallback circle if image is not loaded
        ctx.strokeStyle = DESIGN_TOKENS.purpleGlow;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(0, 0, 65, 0, Math.PI * 2);
        ctx.stroke();
    }
    ctx.restore();
    
    // I
    drawI(ctx, centerX + 80 + dx, centerY + dy);
    
    // D
    drawD(ctx, centerX + 175 + dx, centerY + dy);
    
    // 3. Draw Sovereign Gold Tagline
    ctx.fillStyle = DESIGN_TOKENS.sovereignGold;
    ctx.font = "300 12px 'IBM Plex Mono'";
    ctx.textAlign = "center";
    ctx.letterSpacing = "0.35em";
    ctx.fillText("FORERUNNER COMPANY", centerX, centerY + 120);
    
    // 4. Draw CTA button "ENTER VOID"
    const isHover = mouseX >= centerX - 100 && mouseX <= centerX + 100 && mouseY >= centerY + 180 && mouseY <= centerY + 225;
    
    ctx.save();
    if (isHover) {
        ctx.shadowColor = DESIGN_TOKENS.sovereignGold;
        ctx.shadowBlur = 15;
        ctx.fillStyle = "rgba(244, 213, 141, 0.08)";
        ctx.fillRect(centerX - 100, centerY + 180, 200, 45);
    }
    ctx.strokeStyle = DESIGN_TOKENS.sovereignGold;
    ctx.lineWidth = 1.5;
    ctx.strokeRect(centerX - 100, centerY + 180, 200, 45);
    
    ctx.shadowBlur = 0;
    ctx.fillStyle = isHover ? "#ffffff" : DESIGN_TOKENS.textPrimary;
    ctx.font = "300 11px 'Inter'";
    ctx.letterSpacing = "0.2em";
    ctx.fillText("ENTER VOID", centerX, centerY + 207);
    ctx.restore();
    
    // 5. Draw decorative 4-point star in bottom right
    drawFourPointStar(ctx, canvas.width - 120, canvas.height - 120, 20, 5, "#ffffff");
    
    return isHover ? "pointer" : "default";
}

function renderDownloadPortal(centerX, centerY) {
    // Title
    ctx.fillStyle = DESIGN_TOKENS.textPrimary;
    ctx.font = "bold 32px 'Archivo Black'";
    ctx.textAlign = "center";
    ctx.fillText("DOWNLOAD TRUTH", centerX, centerY - 100);
    
    ctx.fillStyle = DESIGN_TOKENS.sovereignGold;
    ctx.font = "300 12px 'IBM Plex Mono'";
    ctx.fillText("DECENTRALIZED LOCAL WALLED GARDEN", centerX, centerY - 60);
    
    let isHover = false;
    
    // Button 1: Desktop App
    const hoverBtn1 = mouseX >= centerX - 160 && mouseX <= centerX + 160 && mouseY >= centerY - 10 && mouseY <= centerY + 35;
    ctx.save();
    if (hoverBtn1) {
        ctx.shadowColor = DESIGN_TOKENS.purpleGlow;
        ctx.shadowBlur = 15;
        ctx.fillStyle = "rgba(124, 58, 237, 0.08)";
        ctx.fillRect(centerX - 160, centerY - 10, 320, 45);
        isHover = true;
    }
    ctx.strokeStyle = DESIGN_TOKENS.purpleGlow;
    ctx.lineWidth = 1.5;
    ctx.strokeRect(centerX - 160, centerY - 10, 320, 45);
    ctx.fillStyle = hoverBtn1 ? "#ffffff" : DESIGN_TOKENS.textPrimary;
    ctx.font = "13px 'Inter'";
    ctx.letterSpacing = "0.05em";
    ctx.fillText("DOWNLOAD FOR DESKTOP (TRUTH.EXE)", centerX, centerY + 18);
    ctx.restore();
    
    // Button 2: Mobile App
    const hoverBtn2 = mouseX >= centerX - 160 && mouseX <= centerX + 160 && mouseY >= centerY + 60 && mouseY <= centerY + 105;
    ctx.save();
    if (hoverBtn2) {
        ctx.shadowColor = DESIGN_TOKENS.purpleGlow;
        ctx.shadowBlur = 15;
        ctx.fillStyle = "rgba(124, 58, 237, 0.08)";
        ctx.fillRect(centerX - 160, centerY + 60, 320, 45);
        isHover = true;
    }
    ctx.strokeStyle = DESIGN_TOKENS.purpleGlow;
    ctx.lineWidth = 1.5;
    ctx.strokeRect(centerX - 160, centerY + 60, 320, 45);
    ctx.fillStyle = hoverBtn2 ? "#ffffff" : DESIGN_TOKENS.textPrimary;
    ctx.font = "13px 'Inter'";
    ctx.letterSpacing = "0.05em";
    ctx.fillText("DOWNLOAD FOR MOBILE (TRUTH.APK)", centerX, centerY + 88);
    ctx.restore();
    
    // Cancel Link
    const hoverCancel = mouseX >= centerX - 100 && mouseX <= centerX + 100 && mouseY >= centerY + 150 && mouseY <= centerY + 180;
    ctx.save();
    ctx.fillStyle = hoverCancel ? "#ffffff" : "#666";
    ctx.font = "12px 'Inter'";
    ctx.fillText("[ CANCEL AND RETURN ]", centerX, centerY + 168);
    ctx.restore();
    if (hoverCancel) isHover = true;
    
    // Decorative star
    drawFourPointStar(ctx, canvas.width - 120, canvas.height - 120, 20, 5, "#ffffff");
    
    return isHover ? "pointer" : "default";
}

function handleCanvasClick(e) {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    if (currentUIState === "ThresholdLanding") {
        if (x >= centerX - 100 && x <= centerX + 100 && y >= centerY + 180 && y <= centerY + 225) {
            console.log("[VTP] Sending intent packet: enter_void");
            sendVTPIntent("enter_void");
        }
    } else if (currentUIState === "DownloadPortal") {
        if (x >= centerX - 160 && x <= centerX + 160 && y >= centerY - 10 && y <= centerY + 35) {
            console.log("[VTP] Downloading Desktop Client...");
            window.location.href = "/downloads/truth.exe";
        }
        if (x >= centerX - 160 && x <= centerX + 160 && y >= centerY + 60 && y <= centerY + 105) {
            console.log("[VTP] Downloading Mobile Client...");
            window.location.href = "/downloads/truth.apk";
        }
        if (x >= centerX - 100 && x <= centerX + 100 && y >= centerY + 150 && y <= centerY + 180) {
            console.log("[VTP] Sending intent packet: cancel");
            sendVTPIntent("cancel");
        }
    }
}

// Connect to secure VTP stream server
function connectVTPServer() {
    const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
    const wsProto = isLocal ? "ws" : "wss";
    const wsHost = isLocal ? window.location.hostname : "ivoid.app";
    const wsUrl = `${wsProto}://${wsHost}:9000`;
    console.log(`Connecting to VTP stream server at ${wsUrl}...`);
    ws = new WebSocket(wsUrl);
    ws.binaryType = "arraybuffer";
    
    ws.onmessage = function(event) {
        const view = new DataView(event.data);
        const entropyAnchor = view.getUint32(0);
        if (entropyAnchor !== 0xF00DBABE) return;
        
        const stateOffset = 12;
        const stateCode = view.getUint8(stateOffset);
        
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
        if (action === "enter_void") currentUIState = "DownloadPortal";
        else if (action === "cancel") currentUIState = "ThresholdLanding";
        renderUI();
        return;
    }
    
    const packet = new ArrayBuffer(64);
    const view = new DataView(packet);
    view.setUint32(0, 0xF00DBABE);
    
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
    requestAnimationFrame(animationLoop);
};
