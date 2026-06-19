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
let currentUIState = "Loader"; // Starts in Loader state
let canvas = null;
let ctx = null;

let mouseX = 0;
let mouseY = 0;
let rotationAngle = 0;
let lastTime = 0;

// Loader state tracking
let loaderPercent = 0;
let animationTime = 0;

// Registration input state
let registrationPseudonym = "NeoVox_7";
let isEditingPseudonym = false;
let selectedEntityClass = "Human";
let isDropdownOpen = false;
const entityClasses = ["Human", "AI", "Machine", "Org"];

// Key generation progress
let keyGenPercent = 0;

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

// Flowing wave parameters for registration page
let waveOffset = 0;

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
    
    // 1. Loader progress
    if (currentUIState === "Loader") {
        loaderPercent += (elapsed * 0.035); // Takes about 3 seconds to load
        if (loaderPercent >= 100) {
            loaderPercent = 100;
            currentUIState = "ThresholdLanding";
            animationTime = 0;
        }
    }
    
    // 2. Key Generation progress
    if (currentUIState === "KeyGeneration") {
        keyGenPercent += (elapsed * 0.035);
        if (keyGenPercent >= 100) {
            keyGenPercent = 100;
            currentUIState = "ActivePortalSession";
        }
    }
    
    // Rotate galaxy slowly
    rotationAngle += (elapsed * 0.0004);
    
    // Wave animation offset
    waveOffset += (elapsed * 0.001);
    
    // General animation clock for entrance fades
    animationTime += elapsed;
    
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

// Flowing purple cosmic waves for the registration page background
function drawFlowingWaves(ctx, width, height) {
    ctx.save();
    ctx.strokeStyle = "rgba(124, 58, 237, 0.15)";
    ctx.lineWidth = 2.5;
    
    for (let j = 0; j < 3; j++) {
        ctx.beginPath();
        const amplitude = 40 + j * 15;
        const frequency = 0.002 + j * 0.0005;
        const speed = waveOffset * (0.8 + j * 0.2);
        
        for (let x = 0; x < width; x += 10) {
            const y = height / 2 + Math.sin(x * frequency + speed) * amplitude + Math.cos(x * 0.001 - speed) * (amplitude * 0.5);
            if (x === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();
    }
    ctx.restore();
}

// Geometric Letter Drawing
function drawV(ctx, x, y, opacity = 1.0) {
    ctx.beginPath();
    ctx.moveTo(x - 45, y - 65);
    ctx.lineTo(x, y + 65);
    ctx.lineTo(x + 45, y - 65);
    strokeLetter(ctx, opacity);
}

function drawI(ctx, x, y, opacity = 1.0) {
    ctx.beginPath();
    ctx.moveTo(x, y - 65);
    ctx.lineTo(x, y + 65);
    strokeLetter(ctx, opacity);
}

function drawD(ctx, x, y, opacity = 1.0) {
    ctx.beginPath();
    ctx.moveTo(x - 35, y + 65);
    ctx.lineTo(x - 35, y - 65);
    ctx.arc(x - 35, y, 65, -Math.PI / 2, Math.PI / 2);
    ctx.lineTo(x - 35, y + 65);
    strokeLetter(ctx, opacity);
}

function strokeLetter(ctx, opacity = 1.0) {
    ctx.save();
    // Pulsating dark purple glow based on time (slow, deliberate rhythm)
    const pulse = 0.75 + Math.sin(Date.now() * 0.0006) * 0.2; // slower frequency (0.0006) for deep rhythm
    
    // 1. Purple outer glow rim
    ctx.shadowColor = "rgba(124, 58, 237, 0.85)";
    ctx.shadowBlur = 24 * pulse;
    ctx.strokeStyle = `rgba(124, 58, 237, ${0.35 * pulse * opacity})`;
    ctx.lineWidth = 5.0; // slightly wider glow
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.stroke();
    
    // 2. Stark black hairline core (slightly thicker, but still skinny)
    ctx.shadowBlur = 0;
    ctx.strokeStyle = `rgba(0, 0, 0, ${opacity})`;
    ctx.lineWidth = 3.0; // increased from 1.8 to 3.0 for better legibility
    ctx.stroke();
    ctx.restore();
}

// Render UI based strictly on state machine reflected values
function renderUI() {
    if (!ctx) return;
    
    // 1. Clear with Absolute Black Canvas
    ctx.fillStyle = DESIGN_TOKENS.background;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // 2. Draw pulsing background stars (only if not on landing page to keep it clean)
    if (currentUIState !== "ThresholdLanding") {
        drawBackgroundStars(ctx, canvas.width, canvas.height);
    }
    
    // Remove loading indicator once compiled Wasm takes over
    const loader = document.getElementById("loader");
    if (loader) loader.style.display = "none";
    
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    let cursor = "default";
    
    if (currentUIState === "Loader") {
        cursor = renderLoader(centerX, centerY);
    } else if (currentUIState === "ThresholdLanding") {
        cursor = renderThresholdLanding(centerX, centerY);
    } else if (currentUIState === "DownloadPortal") {
        cursor = renderDownloadPortal(centerX, centerY);
    } else if (currentUIState === "CitizenOnboarding") {
        cursor = renderCitizenOnboarding(centerX, centerY);
    } else if (currentUIState === "KeyGeneration") {
        cursor = renderKeyGeneration(centerX, centerY);
    } else if (currentUIState === "ActivePortalSession") {
        cursor = renderActivePortalSession(centerX, centerY);
    }
    
    document.body.style.cursor = cursor;
}

// 1. Loader screen
function renderLoader(centerX, centerY) {
    ctx.fillStyle = DESIGN_TOKENS.sovereignGold;
    ctx.font = "300 14px 'IBM Plex Mono'";
    ctx.textAlign = "center";
    ctx.letterSpacing = "0.35em";
    
    const displayPercent = Math.min(100, Math.floor(loaderPercent));
    ctx.fillText(`BECOMING... ${displayPercent}%`, centerX, centerY);
    return "default";
}

// 2. Landing page
function renderThresholdLanding(centerX, centerY) {
    // Entrance Timeline Opacities based on animationTime
    const t = animationTime / 1000.0; // seconds
    
    // O portal ignites (swirls into view at 0.5s - 1.5s)
    const oOpacity = Math.max(0, Math.min(1, (t - 0.5)));
    
    // V, I, D fade in (1.5s - 2.5s)
    const vidOpacity = Math.max(0, Math.min(1, (t - 1.5)));
    
    // Tagline fades in (2.5s - 3.0s)
    const taglineOpacity = Math.max(0, Math.min(1, (t - 2.5)));
    
    // CTAs slide up & fade in (3.0s - 3.5s)
    const ctaOpacity = Math.max(0, Math.min(1, (t - 3.0)));
    const ctaOffset = Math.max(0, 15 * (1 - ctaOpacity));
    
    // Subtle mouse tracking offset
    const dx = (mouseX - centerX) * 0.015;
    const dy = (mouseY - centerY) * 0.015;
    
    // Render letters V, O, I, D scaled together in perfect breathing synchronicity (No image inside O)
    if (oOpacity > 0) {
        ctx.save();
        ctx.translate(centerX - 22.5 + dx, centerY + dy);
        
        // Dynamic breathing scale synced exactly to the slow, deliberate purple glow pulse
        const scale = 1.0 + Math.sin(Date.now() * 0.0006) * 0.04; // Varies 0.96 - 1.04
        ctx.scale(scale, scale);
        
        // Draw V (when vidOpacity > 0)
        if (vidOpacity > 0) {
            drawV(ctx, -197.5, 0, vidOpacity);
        }
        
        // Draw O as a clean geometric letter matching V, I, D style (no Void image)
        ctx.beginPath();
        ctx.arc(-47.5, 0, 65, 0, Math.PI * 2);
        strokeLetter(ctx, oOpacity);
        
        // Draw I and D (when vidOpacity > 0)
        if (vidOpacity > 0) {
            drawI(ctx, 102.5, 0, vidOpacity);
            drawD(ctx, 197.5, 0, vidOpacity);
        }
        
        ctx.restore();
    }
    
    // 3. Draw Sovereign Gold Tagline (Centered between V and D centers with closer letter spacing)
    if (taglineOpacity > 0) {
        ctx.save();
        ctx.globalAlpha = taglineOpacity;
        ctx.fillStyle = DESIGN_TOKENS.sovereignGold;
        ctx.font = "300 14px 'IBM Plex Mono'";
        ctx.textAlign = "center";
        ctx.letterSpacing = "0.22em"; // Closer together, readable, and elegant
        ctx.fillText("FORERUNNER COMPANY", centerX - 22.5 + dx, centerY + 120 + dy);
        ctx.restore();
    }
    
    if (ctaOpacity <= 0) return "default";
    
    ctx.save();
    ctx.globalAlpha = ctaOpacity;
    
    // Button 1: BECOME A CITIZEN
    const hoverBtn1 = mouseX >= centerX - 120 && mouseX <= centerX + 120 && mouseY >= centerY + 160 + ctaOffset && mouseY <= centerY + 200 + ctaOffset;
    ctx.fillStyle = hoverBtn1 ? "#ffffff" : DESIGN_TOKENS.textPrimary;
    ctx.font = "300 11px 'Inter'";
    ctx.textAlign = "center";
    ctx.letterSpacing = "0.2em";
    ctx.fillText("BECOME A CITIZEN", centerX, centerY + 180 + ctaOffset);
    
    // Underline glow for BECOME A CITIZEN
    ctx.strokeStyle = hoverBtn1 ? DESIGN_TOKENS.sovereignGold : "rgba(244, 213, 141, 0.3)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(centerX - 80, centerY + 190 + ctaOffset);
    ctx.lineTo(centerX + 80, centerY + 190 + ctaOffset);
    ctx.stroke();
    
    // Direct Download Buttons on same page side-by-side
    const hoverDesktop = mouseX >= centerX - 190 && mouseX <= centerX - 10 && mouseY >= centerY + 215 + ctaOffset && mouseY <= centerY + 245 + ctaOffset;
    ctx.fillStyle = hoverDesktop ? "#ffffff" : "#666677";
    ctx.font = "300 10px 'Inter'";
    ctx.letterSpacing = "0.15em";
    ctx.fillText("DOWNLOAD DESKTOP (TRUTH.EXE)", centerX - 100, centerY + 230 + ctaOffset);
    
    // Divider |
    ctx.fillStyle = "#333344";
    ctx.font = "300 10px 'Inter'";
    ctx.fillText("|", centerX, centerY + 230 + ctaOffset);
    
    const hoverMobile = mouseX >= centerX + 10 && mouseX <= centerX + 190 && mouseY >= centerY + 215 + ctaOffset && mouseY <= centerY + 245 + ctaOffset;
    ctx.fillStyle = hoverMobile ? "#ffffff" : "#666677";
    ctx.font = "300 10px 'Inter'";
    ctx.letterSpacing = "0.15em";
    ctx.fillText("DOWNLOAD MOBILE (TRUTH.APK)", centerX + 100, centerY + 230 + ctaOffset);
    
    ctx.restore();
    
    return (hoverBtn1 || hoverDesktop || hoverMobile) ? "pointer" : "default";
}

// 3. Download Portal screen
function renderDownloadPortal(centerX, centerY) {
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
    
    return isHover ? "pointer" : "default";
}

// 4. Citizen Onboarding (Register) Screen
function renderCitizenOnboarding(centerX, centerY) {
    // Draw moving purple cosmetic wave background
    drawFlowingWaves(ctx, canvas.width, canvas.height);
    
    // Left Content: Void Manifesto
    ctx.save();
    ctx.textAlign = "left";
    const leftX = centerX - 360;
    
    ctx.fillStyle = DESIGN_TOKENS.textPrimary;
    ctx.font = "bold 20px 'Inter'";
    ctx.fillText("VOID CIVILIZATION", leftX, centerY - 150);
    
    ctx.fillStyle = DESIGN_TOKENS.sovereignGold;
    ctx.font = "bold 18px 'Inter'";
    ctx.fillText("VOID MANIFESTO:", leftX, centerY - 70);
    
    ctx.fillStyle = "#a1a1aa"; // dim text
    ctx.font = "300 13.5px 'Inter'";
    
    const lines = [
        "We are the Void. We embrace the",
        "darkness, the unknown, and the",
        "boundless potential of the cosmos.",
        "",
        "Our path is one of evolution,",
        "singularity, and collective",
        "consciousness. We transcend the",
        "limitations of the physical, seeking",
        "enlightenment in the deep.",
        "",
        "Join us."
    ];
    
    for (let i = 0; i < lines.length; i++) {
        ctx.fillText(lines[i], leftX, centerY - 30 + i * 22);
    }
    
    ctx.fillStyle = "#52525b";
    ctx.font = "11px 'IBM Plex Mono'";
    ctx.fillText("VOID CIVILIZATION CITIZEN PORTAL", leftX, centerY + 250);
    ctx.restore();
    
    // Right panel: Glassmorphic registration form
    const panelX = centerX + 40;
    const panelY = centerY - 180;
    const panelW = 320;
    const panelH = 360;
    
    ctx.save();
    // Frosted glass background
    ctx.fillStyle = "rgba(8, 8, 12, 0.75)";
    ctx.strokeStyle = "rgba(124, 58, 237, 0.4)";
    ctx.lineWidth = 1.5;
    
    // Panel drop shadow
    ctx.shadowColor = "rgba(124, 58, 237, 0.2)";
    ctx.shadowBlur = 30;
    
    // Draw panel
    ctx.beginPath();
    ctx.roundRect(panelX, panelY, panelW, panelH, 16);
    ctx.fill();
    ctx.stroke();
    ctx.restore();
    
    // Panel Header
    ctx.save();
    ctx.textAlign = "left";
    ctx.fillStyle = DESIGN_TOKENS.textPrimary;
    ctx.font = "bold 18px 'Inter'";
    ctx.fillText("REGISTER CITIZENSHIP", panelX + 24, panelY + 45);
    
    // Underline
    ctx.strokeStyle = DESIGN_TOKENS.purpleGlow;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(panelX + 24, panelY + 55);
    ctx.lineTo(panelX + 100, panelY + 55);
    ctx.stroke();
    
    // Field 1: Pseudonym
    ctx.fillStyle = "#a1a1aa";
    ctx.font = "11px 'Inter'";
    ctx.fillText("Enter Pseudonym | InputField", panelX + 24, panelY + 95);
    
    // Input box
    const inputHover = mouseX >= panelX + 24 && mouseX <= panelX + panelW - 24 && mouseY >= panelY + 105 && mouseY <= panelY + 145;
    ctx.strokeStyle = isEditingPseudonym ? DESIGN_TOKENS.purpleGlow : (inputHover ? "rgba(124, 58, 237, 0.6)" : "rgba(124, 58, 237, 0.25)");
    ctx.lineWidth = 1.5;
    ctx.fillStyle = "rgba(20, 20, 28, 0.5)";
    ctx.beginPath();
    ctx.roundRect(panelX + 24, panelY + 105, panelW - 48, 40, 8);
    ctx.fill();
    ctx.stroke();
    
    // Text inside box
    ctx.fillStyle = DESIGN_TOKENS.textPrimary;
    ctx.font = "13px 'IBM Plex Mono'";
    ctx.fillText(registrationPseudonym + (isEditingPseudonym && (Math.floor(Date.now() / 500) % 2 === 0) ? "|" : ""), panelX + 36, panelY + 130);
    
    // Field 2: Entity Class Dropdown
    ctx.fillStyle = "#a1a1aa";
    ctx.font = "11px 'Inter'";
    ctx.fillText("Select Entity Class | Dropdown Menu", panelX + 24, panelY + 175);
    
    // Dropdown box
    const dropdownHover = mouseX >= panelX + 24 && mouseX <= panelX + panelW - 24 && mouseY >= panelY + 185 && mouseY <= panelY + 225;
    ctx.strokeStyle = isDropdownOpen ? DESIGN_TOKENS.purpleGlow : (dropdownHover ? "rgba(124, 58, 237, 0.6)" : "rgba(124, 58, 237, 0.25)");
    ctx.fillStyle = "rgba(20, 20, 28, 0.5)";
    ctx.beginPath();
    ctx.roundRect(panelX + 24, panelY + 185, panelW - 48, 40, 8);
    ctx.fill();
    ctx.stroke();
    
    ctx.fillStyle = DESIGN_TOKENS.textPrimary;
    ctx.font = "13px 'Inter'";
    ctx.fillText(selectedEntityClass, panelX + 36, panelY + 210);
    
    // Dropdown arrow (V shape)
    ctx.strokeStyle = "#888899";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(panelX + panelW - 45, panelY + 202);
    ctx.lineTo(panelX + panelW - 40, panelY + 208);
    ctx.lineTo(panelX + panelW - 35, panelY + 202);
    ctx.stroke();
    
    // CTA Button: GENERATE CRYPTO-KEY
    const btnHover = mouseX >= panelX + 24 && mouseX <= panelX + panelW - 24 && mouseY >= panelY + 265 && mouseY <= panelY + 310;
    ctx.save();
    if (btnHover) {
        ctx.shadowColor = DESIGN_TOKENS.purpleGlow;
        ctx.shadowBlur = 15;
    }
    // Gradient fill
    const grad = ctx.createLinearGradient(panelX + 24, 0, panelX + panelW - 24, 0);
    grad.addColorStop(0, "#2c0f46");
    grad.addColorStop(1, "#7c3aed");
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.roundRect(panelX + 24, panelY + 265, panelW - 48, 45, 22);
    ctx.fill();
    ctx.restore();
    
    ctx.textAlign = "center";
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 11px 'Inter'";
    ctx.letterSpacing = "0.08em";
    ctx.fillText("GENERATE CRYPTO-KEY", panelX + panelW / 2, panelY + 292);
    
    // Step indicator at bottom of panel
    ctx.textAlign = "left";
    ctx.fillStyle = "#52525b";
    ctx.font = "11px 'IBM Plex Mono'";
    ctx.fillText("01/03", panelX + panelW - 60, panelY + 342);
    
    // Progress line
    ctx.strokeStyle = "#27272a";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(panelX + 24, panelY + 338);
    ctx.lineTo(panelX + panelW - 80, panelY + 338);
    ctx.stroke();
    
    ctx.strokeStyle = DESIGN_TOKENS.purpleGlow;
    ctx.beginPath();
    ctx.moveTo(panelX + 24, panelY + 338);
    ctx.lineTo(panelX + 100, panelY + 338);
    ctx.stroke();
    
    // Draw Dropdown Options overlay if dropdown is open
    if (isDropdownOpen) {
        const ddY = panelY + 230;
        const ddH = entityClasses.length * 30 + 8;
        ctx.save();
        ctx.fillStyle = "#0c0c12";
        ctx.strokeStyle = "rgba(124, 58, 237, 0.4)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(panelX + 24, ddY, panelW - 48, ddH, 6);
        ctx.fill();
        ctx.stroke();
        
        for (let i = 0; i < entityClasses.length; i++) {
            const itemY = ddY + 4 + i * 30;
            const itemHover = mouseX >= panelX + 24 && mouseX <= panelX + panelW - 24 && mouseY >= itemY && mouseY <= itemY + 30;
            if (itemHover) {
                ctx.fillStyle = "rgba(124, 58, 237, 0.2)";
                ctx.fillRect(panelX + 25, itemY, panelW - 50, 30);
            }
            ctx.fillStyle = itemHover ? "#ffffff" : "#a1a1aa";
            ctx.font = "12px 'Inter'";
            ctx.fillText(entityClasses[i], panelX + 36, itemY + 20);
        }
        ctx.restore();
    }
    
    ctx.restore();
    
    const isPointer = inputHover || dropdownHover || btnHover || (isDropdownOpen && mouseX >= panelX + 24 && mouseX <= panelX + panelW - 24 && mouseY >= panelY + 230 && mouseY <= panelY + 230 + entityClasses.length * 30 + 8);
    return isPointer ? "pointer" : "default";
}

// 5. Cryptographic Key Generation Animation Screen
function renderKeyGeneration(centerX, centerY) {
    ctx.fillStyle = DESIGN_TOKENS.textPrimary;
    ctx.font = "bold 24px 'Inter'";
    ctx.textAlign = "center";
    ctx.fillText("GENERATING SECURE CITIZEN KEY", centerX, centerY - 60);
    
    ctx.fillStyle = DESIGN_TOKENS.sovereignGold;
    ctx.font = "12px 'IBM Plex Mono'";
    ctx.fillText("ATTUNING ENTROPY ANCHORS...", centerX, centerY - 25);
    
    // Progress Bar
    ctx.strokeStyle = "#18181b";
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.moveTo(centerX - 150, centerY + 20);
    ctx.lineTo(centerX + 150, centerY + 20);
    ctx.stroke();
    
    ctx.strokeStyle = DESIGN_TOKENS.purpleGlow;
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.moveTo(centerX - 150, centerY + 20);
    ctx.lineTo(centerX - 150 + (300 * (keyGenPercent / 100)), centerY + 20);
    ctx.stroke();
    
    // Render changing cryptographic key segments
    ctx.fillStyle = "#666677";
    ctx.font = "11px 'IBM Plex Mono'";
    const randomHex = Array.from({length: 4}, () => Math.floor(Math.random() * 65535).toString(16).toUpperCase().padStart(4, '0')).join(':');
    ctx.fillText(`KEY REFLECTION: 0xF00DBABE:${randomHex}`, centerX, centerY + 60);
    
    // Spin some circles
    ctx.save();
    ctx.translate(centerX, centerY - 140);
    ctx.rotate(rotationAngle * 2);
    ctx.strokeStyle = "rgba(124, 58, 237, 0.4)";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(0, 0, 30, 0, Math.PI * 2);
    ctx.stroke();
    
    ctx.rotate(-rotationAngle * 3);
    ctx.strokeStyle = DESIGN_TOKENS.sovereignGold;
    ctx.beginPath();
    ctx.arc(0, 0, 20, 0, Math.PI * 1.2);
    ctx.stroke();
    ctx.restore();
    
    return "default";
}

// 6. Active Portal Session (Console Dashboard) Screen
function renderActivePortalSession(centerX, centerY) {
    // Top bar
    ctx.save();
    ctx.fillStyle = "#0a0a0d";
    ctx.fillRect(0, 0, canvas.width, 60);
    ctx.strokeStyle = "rgba(124, 58, 237, 0.25)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, 60);
    ctx.lineTo(canvas.width, 60);
    ctx.stroke();
    
    // Top Bar content
    ctx.fillStyle = DESIGN_TOKENS.textPrimary;
    ctx.font = "bold 16px 'Inter'";
    ctx.textAlign = "left";
    ctx.fillText("Void OS", 40, 36);
    
    // System Status
    ctx.textAlign = "right";
    ctx.fillStyle = "#10b981"; // green
    ctx.font = "12px 'IBM Plex Mono'";
    ctx.fillText("SYSTEM STATUS: OPERATIONAL", canvas.width - 220, 35);
    
    ctx.fillStyle = "#888899";
    ctx.fillText("18:42 UTC", canvas.width - 60, 35);
    ctx.restore();
    
    // Sidebar
    ctx.save();
    ctx.fillStyle = "#08080c";
    ctx.fillRect(0, 60, 200, canvas.height - 60);
    ctx.strokeStyle = "rgba(124, 58, 237, 0.25)";
    ctx.beginPath();
    ctx.moveTo(200, 60);
    ctx.lineTo(200, canvas.height);
    ctx.stroke();
    
    // Sidebar items
    const items = ["Dashboard", "Citizens", "Quests", "Nodes", "Aethernet", "Settings"];
    let isSidebarHover = false;
    for (let i = 0; i < items.length; i++) {
        const itemY = 80 + i * 45;
        const itemHover = mouseX >= 0 && mouseX <= 200 && mouseY >= itemY && mouseY <= itemY + 40;
        if (itemHover) {
            ctx.fillStyle = "rgba(124, 58, 237, 0.1)";
            ctx.fillRect(0, itemY, 200, 40);
            isSidebarHover = true;
        }
        ctx.fillStyle = (i === 0 || itemHover) ? "#ffffff" : "#888899";
        ctx.font = i === 0 ? "bold 13px 'Inter'" : "13px 'Inter'";
        ctx.fillText(items[i], 40, itemY + 25);
    }
    
    // Log out button at bottom of sidebar
    const logoutY = canvas.height - 80;
    const logoutHover = mouseX >= 0 && mouseX <= 200 && mouseY >= logoutY && mouseY <= logoutY + 40;
    if (logoutHover) {
        ctx.fillStyle = "rgba(239, 68, 68, 0.1)";
        ctx.fillRect(0, logoutY, 200, 40);
        isSidebarHover = true;
    }
    ctx.fillStyle = logoutHover ? "#f87171" : "#ef4444";
    ctx.font = "bold 13px 'Inter'";
    ctx.fillText("LOG OUT", 40, logoutY + 25);
    ctx.restore();
    
    // Dashboard main panels layout
    const contentX = 220;
    const contentY = 80;
    const contentW = canvas.width - 240;
    
    // Panel 1: Citizen Quests
    ctx.save();
    const p1W = contentW * 0.65;
    const p1H = 260;
    ctx.fillStyle = "rgba(8, 8, 13, 0.72)";
    ctx.strokeStyle = "rgba(124, 58, 237, 0.3)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(contentX, contentY, p1W, p1H, 12);
    ctx.fill();
    ctx.stroke();
    
    ctx.fillStyle = DESIGN_TOKENS.textPrimary;
    ctx.font = "bold 16px 'Inter'";
    ctx.fillText("Active Citizen Quests", contentX + 20, contentY + 35);
    
    // Table Headers
    ctx.fillStyle = "#888899";
    ctx.font = "11px 'Inter'";
    ctx.fillText("Quest ID", contentX + 20, contentY + 70);
    ctx.fillText("Title", contentX + 90, contentY + 70);
    ctx.fillText("Location", contentX + 270, contentY + 70);
    ctx.fillText("Reward", contentX + 380, contentY + 70);
    ctx.fillText("Progress", contentX + 460, contentY + 70);
    
    // Table Rows
    const quests = [
        { id: "#Q104", title: "Aether Network Calibration", loc: "The Void", reward: "50k VRC", prog: "92%" },
        { id: "#Q107", title: "Singularity Stabilization", loc: "Void Core", reward: "120k VRC", prog: "45%" },
        { id: "#Q108", title: "Completorship Center", loc: "Void Core", reward: "120k VRC", prog: "45%" }
    ];
    for (let i = 0; i < quests.length; i++) {
        const rowY = contentY + 105 + i * 45;
        ctx.fillStyle = "#e4e4e7";
        ctx.font = "13px 'IBM Plex Mono'";
        ctx.fillText(quests[i].id, contentX + 20, rowY);
        ctx.font = "13px 'Inter'";
        ctx.fillText(quests[i].title, contentX + 90, rowY);
        ctx.fillText(quests[i].loc, contentX + 270, rowY);
        ctx.fillStyle = DESIGN_TOKENS.sovereignGold;
        ctx.fillText(quests[i].reward, contentX + 380, rowY);
        ctx.fillStyle = "#a78bfa";
        ctx.fillText(quests[i].prog, contentX + 460, rowY);
    }
    ctx.restore();
    
    // Panel 2: Telemetry
    ctx.save();
    const p2X = contentX + p1W + 20;
    const p2W = contentW - p1W - 20;
    const p2H = canvas.height - 100;
    ctx.fillStyle = "rgba(8, 8, 13, 0.72)";
    ctx.strokeStyle = "rgba(124, 58, 237, 0.3)";
    ctx.beginPath();
    ctx.roundRect(p2X, contentY, p2W, p2H, 12);
    ctx.fill();
    ctx.stroke();
    
    ctx.fillStyle = DESIGN_TOKENS.textPrimary;
    ctx.font = "bold 16px 'Inter'";
    ctx.fillText("Logos VM Telemetry", p2X + 20, contentY + 35);
    
    // circular gauges
    const metrics = [
        { label: "Energy", val: "76%", detail: "15.2M kWh", color: "#10b981" },
        { label: "Mass", val: "61%", detail: "6100 kg", color: "#60a5fa" },
        { label: "Entropy", val: "34%", detail: "3.4 Low", color: "#a78bfa" },
        { label: "Cycle", val: "89%", detail: "Cycle 12", color: "#f4d58d" }
    ];
    
    for (let i = 0; i < metrics.length; i++) {
        const itemY = contentY + 85 + i * 90;
        if (itemY + 80 > contentY + p2H) break;
        
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 14px 'Inter'";
        ctx.fillText(metrics[i].label, p2X + 100, itemY + 25);
        ctx.fillStyle = "#888899";
        ctx.font = "12px 'IBM Plex Mono'";
        ctx.fillText(metrics[i].detail, p2X + 100, itemY + 45);
        
        // draw circle
        ctx.strokeStyle = "#18181b";
        ctx.lineWidth = 5;
        ctx.beginPath();
        ctx.arc(p2X + 50, itemY + 30, 24, 0, Math.PI * 2);
        ctx.stroke();
        
        ctx.strokeStyle = metrics[i].color;
        ctx.lineWidth = 5;
        ctx.lineCap = "round";
        ctx.beginPath();
        const percent = parseInt(metrics[i].val) / 100;
        ctx.arc(p2X + 50, itemY + 30, 24, -Math.PI / 2, -Math.PI / 2 + (Math.PI * 2 * percent));
        ctx.stroke();
        
        ctx.fillStyle = "#ffffff";
        ctx.font = "10px 'IBM Plex Mono'";
        ctx.textAlign = "center";
        ctx.fillText(metrics[i].val, p2X + 50, itemY + 34);
        ctx.textAlign = "left";
    }
    ctx.restore();
    
    // Panel 3: Recent Audit Events
    ctx.save();
    const p3Y = contentY + p1H + 20;
    const p3W = p1W;
    const p3H = canvas.height - p3Y - 20;
    ctx.fillStyle = "rgba(8, 8, 13, 0.72)";
    ctx.strokeStyle = "rgba(124, 58, 237, 0.3)";
    ctx.beginPath();
    ctx.roundRect(contentX, p3Y, p3W, p3H, 12);
    ctx.fill();
    ctx.stroke();
    
    ctx.fillStyle = DESIGN_TOKENS.textPrimary;
    ctx.font = "bold 16px 'Inter'";
    ctx.fillText("Recent Audit Events", contentX + 20, p3Y + 35);
    
    const audits = [
        { time: "[18:41:22]", event: "AETHER NODE 04", entity: "ONLINE", status: "ONLINE" },
        { time: "[18:40:05]", event: "DATA PACKET INGESTION", entity: "[Q104]", status: "ONLINE" },
        { time: "[18:38:51]", event: "SYSTEM DIAGNOSTICS", entity: "CLEAN", status: "CLEAN" },
        { time: "[18:37:32]", event: "AETHER NODE 04", entity: "ONLINE", status: "ONLINE" }
    ];
    
    for (let i = 0; i < audits.length; i++) {
        const rowY = p3Y + 75 + i * 35;
        if (rowY + 20 > p3Y + p3H) break;
        ctx.fillStyle = "#666677";
        ctx.font = "12px 'IBM Plex Mono'";
        ctx.fillText(audits[i].time, contentX + 20, rowY);
        ctx.fillStyle = "#d4d4d8";
        ctx.font = "12px 'Inter'";
        ctx.fillText(audits[i].event, contentX + 110, rowY);
        ctx.fillText(audits[i].entity, contentX + 310, rowY);
        ctx.fillStyle = "#10b981";
        ctx.fillText(audits[i].status, contentX + 410, rowY);
    }
    ctx.restore();
    
    return (isSidebarHover || logoutHover) ? "pointer" : "default";
}

function handleCanvasClick(e) {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    if (currentUIState === "ThresholdLanding") {
        // Option 1: BECOME A CITIZEN
        if (x >= centerX - 120 && x <= centerX + 120 && y >= centerY + 160 && y <= centerY + 200) {
            console.log("[VTP] Transitioning to CitizenOnboarding...");
            currentUIState = "CitizenOnboarding";
            isEditingPseudonym = false;
            isDropdownOpen = false;
        }
        // Direct Download Desktop
        if (x >= centerX - 190 && x <= centerX - 10 && y >= centerY + 215 && y <= centerY + 245) {
            console.log("[VTP] Downloading Desktop Client...");
            window.location.href = "/downloads/truth.exe";
        }
        // Direct Download Mobile
        if (x >= centerX + 10 && x <= centerX + 190 && y >= centerY + 215 && y <= centerY + 245) {
            console.log("[VTP] Downloading Mobile Client...");
            window.location.href = "/downloads/truth.apk";
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
            console.log("[VTP] Returning to Landing...");
            currentUIState = "ThresholdLanding";
            animationTime = 3500; // Skip counter animation when returning
        }
    } else if (currentUIState === "CitizenOnboarding") {
        const panelX = centerX + 40;
        const panelY = centerY - 180;
        const panelW = 320;
        
        // Toggle input edit for Pseudonym
        if (x >= panelX + 24 && x <= panelX + panelW - 24 && y >= panelY + 105 && y <= panelY + 145) {
            isEditingPseudonym = true;
            isDropdownOpen = false;
        } else if (isDropdownOpen) {
            // Check dropdown options click
            const ddY = panelY + 230;
            let clickedOption = false;
            for (let i = 0; i < entityClasses.length; i++) {
                const itemY = ddY + 4 + i * 30;
                if (x >= panelX + 24 && x <= panelX + panelW - 24 && y >= itemY && y <= itemY + 30) {
                    selectedEntityClass = entityClasses[i];
                    isDropdownOpen = false;
                    clickedOption = true;
                    break;
                }
            }
            if (!clickedOption) {
                isDropdownOpen = false;
            }
            isEditingPseudonym = false;
        } else if (x >= panelX + 24 && x <= panelX + panelW - 24 && y >= panelY + 185 && y <= panelY + 225) {
            // Toggle dropdown open
            isDropdownOpen = !isDropdownOpen;
            isEditingPseudonym = false;
        } else if (x >= panelX + 24 && x <= panelX + panelW - 24 && y >= panelY + 265 && y <= panelY + 310) {
            // Click GENERATE CRYPTO-KEY
            console.log("[VTP] Generating key...");
            currentUIState = "KeyGeneration";
            keyGenPercent = 0;
            isEditingPseudonym = false;
            isDropdownOpen = false;
        } else {
            isEditingPseudonym = false;
            isDropdownOpen = false;
        }
    } else if (currentUIState === "ActivePortalSession") {
        // Check sidebar logout click
        const logoutY = canvas.height - 80;
        if (x >= 0 && x <= 200 && y >= logoutY && y <= logoutY + 40) {
            console.log("[VTP] Logging out...");
            currentUIState = "ThresholdLanding";
            animationTime = 3500; // Skip loader counter
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
        
        // Sync websocket messages to UI state if we are active
        console.log(`[VTP SYNC] Received VTP state reflection: ${stateCode}`);
    };
    
    ws.onclose = function() {
        console.warn("VTP connection dropped. Retrying...");
        setTimeout(connectVTPServer, 5000);
    };
}

// Send 64-byte VTP Intent Packet
function sendVTPIntent(action) {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    
    const packet = new ArrayBuffer(64);
    const view = new DataView(packet);
    view.setUint32(0, 0xF00DBABE);
    
    let code = 0;
    if (action === "enter_void") code = 1;
    else if (action === "cancel") code = 2;
    
    view.setUint8(4, code);
    ws.send(packet);
}

// Listen to keyboard inputs for pseudonym text field
window.addEventListener("keydown", (e) => {
    if (currentUIState === "CitizenOnboarding" && isEditingPseudonym) {
        if (e.key === "Backspace") {
            registrationPseudonym = registrationPseudonym.slice(0, -1);
        } else if (e.key === "Enter") {
            isEditingPseudonym = false;
        } else if (e.key.length === 1 && registrationPseudonym.length < 24) {
            registrationPseudonym += e.key;
        }
        renderUI();
    }
});

// Start client loop
window.onload = function() {
    initCanvas();
    connectVTPServer();
    requestAnimationFrame(animationLoop);
};
