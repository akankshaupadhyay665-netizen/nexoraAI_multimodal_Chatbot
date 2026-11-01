/**
 * NEXORA AI - 3D Futuristic Full-Body Humanoid AI Robot Assistant
 * Rendered using Three.js and WebGL
 *
 * Full Anatomical Geometry:
 * - Head (sculpted cranium, faceplate, glowing cyan LED visor eyes, mouth visualizer, sensor ears)
 * - Neck (articulated dark titanium cervical joint with glowing collar ring)
 * - Torso (metallic white & silver armor, collar mantle, abdominal hydraulics, glowing chest Arc Reactor)
 * - Shoulders (metallic deltoid armor pauldrons with cyan LED accents)
 * - Upper arms (biceps cylinders with chrome mechanical pivots)
 * - Forearms (tapered cybernetic forearm bracers)
 * - Hands (palm core with articulated robotic fingers)
 * - Pelvis & Hip Joints (heavy mechanical hip axis)
 * - Legs (quadriceps upper thighs, articulated knee joints with kneepad armor, shin/calf lower legs)
 * - Feet (futuristic magnetic boots with glowing cyan hover sole thrusters)
 * - Futuristic Holographic Platform (dual rotating neon geometric hex grid, energy rings, and particle field)
 *
 * 6 Reactive States: Idle, Thinking, Listening, Speaking, Greeting, Processing
 */

class NexoraRobot {
    constructor(containerId) {
        this.containerId = containerId || "robot-canvas-container";
        this.container = document.getElementById(this.containerId);
        if (!this.container) {
            console.error(`[Nexora 3D Robot] Container #${this.containerId} not found in DOM`);
            return;
        }

        this.state = "idle";
        this.clock = new THREE.Clock();
        this.mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
        this.speechIntensity = 0;
        this.isSpeaking = false;

        this.init();
    }

    init() {
        console.log("[Nexora 3D Robot] Initializing full-body humanoid Three.js scene...");

        // 1. Scene & Environment
        this.scene = new THREE.Scene();
        this.scene.fog = new THREE.FogExp2(0x070913, 0.025);

        const width = this.container.clientWidth || 450;
        const height = this.container.clientHeight || 750;

        // 2. Camera Setup (Frames entire humanoid body from head to feet)
        this.camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 100);
        this.camera.position.set(0, 0.72, 4.8);
        this.camera.lookAt(0, 0.65, 0);

        // 3. WebGL Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.35;
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

        this.container.innerHTML = "";
        this.container.appendChild(this.renderer.domElement);

        // 4. Studio Sci-Fi Lighting
        this.setupLighting();

        // 5. Build Complete Humanoid Robot (Head to Toe)
        this.buildHumanoidRobot();

        // 6. Build Holographic Hover Platform & Particles
        this.buildHoverPlatform();
        this.buildHolographicField();

        // 7. Event Handlers & Window Resizing
        window.addEventListener("resize", () => this.onWindowResize());
        window.addEventListener("mousemove", (e) => this.onMouseMove(e));

        if (window.ResizeObserver) {
            this.resizeObserver = new ResizeObserver(() => this.onWindowResize());
            this.resizeObserver.observe(this.container);
        }

        // Trigger immediate resize updates
        this.onWindowResize();
        setTimeout(() => this.onWindowResize(), 100);
        setTimeout(() => this.onWindowResize(), 400);

        // 8. Welcome Greeting Animation on load
        setTimeout(() => {
            this.setState("greeting");
            setTimeout(() => {
                if (this.state === "greeting") this.setState("idle");
            }, 3500);
        }, 800);

        // 9. Start Render Loop
        this.animate();
        console.log("[Nexora 3D Robot] Full-body humanoid robot successfully initialized.");
    }

    setupLighting() {
        const ambient = new THREE.AmbientLight(0x161e38, 1.4);
        this.scene.add(ambient);

        // Key light (Cyan highlight)
        this.keyLight = new THREE.DirectionalLight(0x00f2fe, 2.6);
        this.keyLight.position.set(3, 4, 4);
        this.scene.add(this.keyLight);

        // Fill light (Electric Purple)
        this.fillLight = new THREE.DirectionalLight(0x8b5cf6, 2.2);
        this.fillLight.position.set(-3, 2, -2);
        this.scene.add(this.fillLight);

        // Rim light (Pure White Backlight)
        this.rimLight = new THREE.DirectionalLight(0xffffff, 2.0);
        this.rimLight.position.set(0, 5, -4);
        this.scene.add(this.rimLight);

        // Chest Core Point Light (Pulsing Nexora Arc Reactor)
        this.coreLight = new THREE.PointLight(0x00f2fe, 2.2, 4);
        this.coreLight.position.set(0, 1.25, 0.45);
        this.scene.add(this.coreLight);
    }

    buildHumanoidRobot() {
        this.robotGroup = new THREE.Group();
        this.scene.add(this.robotGroup);

        // PBR Materials: Metallic White/Silver Armor & Dark Titanium Skeleton
        const armorMat = new THREE.MeshStandardMaterial({
            color: 0xf5f8fc,
            metalness: 0.88,
            roughness: 0.16,
            envMapIntensity: 1.0
        });

        const darkMetalMat = new THREE.MeshStandardMaterial({
            color: 0x121724,
            metalness: 0.92,
            roughness: 0.28
        });

        const chromeMat = new THREE.MeshStandardMaterial({
            color: 0xdde6ed,
            metalness: 0.96,
            roughness: 0.08
        });

        const cyanGlowMat = new THREE.MeshBasicMaterial({ color: 0x00f2fe });
        const purpleGlowMat = new THREE.MeshBasicMaterial({ color: 0xa855f7 });

        // ================= 1. HEAD & FACE =================
        this.headGroup = new THREE.Group();
        this.headGroup.position.set(0, 1.82, 0);

        // Cranium / Helmet
        const craniumGeo = new THREE.SphereGeometry(0.28, 32, 24);
        craniumGeo.scale(0.95, 1.12, 1.05);
        const cranium = new THREE.Mesh(craniumGeo, armorMat);
        this.headGroup.add(cranium);

        // Sleek Curved Visor Screen (Dark tinted glass)
        const visorGeo = new THREE.SphereGeometry(0.25, 32, 16, 0, Math.PI);
        visorGeo.scale(0.92, 0.78, 1.0);
        const visorMat = new THREE.MeshPhysicalMaterial({
            color: 0x050711,
            metalness: 0.92,
            roughness: 0.04,
            transmission: 0.25,
            reflectivity: 0.95
        });
        const visor = new THREE.Mesh(visorGeo, visorMat);
        visor.rotation.y = Math.PI;
        visor.position.set(0, 0.02, 0.06);
        this.headGroup.add(visor);

        // Glowing LED Visor Eyes (Cyan glowing ocular lenses)
        this.eyesGroup = new THREE.Group();
        this.eyesGroup.position.set(0, 0.05, 0.25);

        const eyeGeo = new THREE.SphereGeometry(0.042, 16, 16);
        eyeGeo.scale(1.7, 0.85, 0.6);
        const eyeMat = new THREE.MeshBasicMaterial({ color: 0x00f2fe });

        this.leftEye = new THREE.Mesh(eyeGeo, eyeMat);
        this.leftEye.rotation.z = Math.PI / 2;
        this.leftEye.position.set(-0.09, 0, 0);
        this.eyesGroup.add(this.leftEye);

        this.rightEye = new THREE.Mesh(eyeGeo, eyeMat);
        this.rightEye.rotation.z = Math.PI / 2;
        this.rightEye.position.set(0.09, 0, 0);
        this.eyesGroup.add(this.rightEye);

        this.headGroup.add(this.eyesGroup);

        // Audio Visualizer Mouth Strip (Reacts to speech output)
        const mouthGeo = new THREE.BoxGeometry(0.11, 0.015, 0.02);
        this.mouthMesh = new THREE.Mesh(mouthGeo, cyanGlowMat);
        this.mouthMesh.position.set(0, -0.11, 0.25);
        this.headGroup.add(this.mouthMesh);

        // Sensor Nodes (Ears)
        const earGeo = new THREE.CylinderGeometry(0.035, 0.055, 0.1, 16);
        const leftEar = new THREE.Mesh(earGeo, darkMetalMat);
        leftEar.rotation.z = Math.PI / 2;
        leftEar.position.set(-0.29, 0.04, 0);
        this.headGroup.add(leftEar);

        const rightEar = new THREE.Mesh(earGeo, darkMetalMat);
        rightEar.rotation.z = -Math.PI / 2;
        rightEar.position.set(0.29, 0.04, 0);
        this.headGroup.add(rightEar);

        // Neck Joint with glowing collar ring
        const neckGeo = new THREE.CylinderGeometry(0.09, 0.11, 0.16, 16);
        const neck = new THREE.Mesh(neckGeo, darkMetalMat);
        neck.position.set(0, -0.2, 0);
        this.headGroup.add(neck);

        const neckRingGeo = new THREE.TorusGeometry(0.105, 0.012, 12, 24);
        neckRingGeo.rotateX(Math.PI / 2);
        const neckRing = new THREE.Mesh(neckRingGeo, cyanGlowMat);
        neckRing.position.set(0, -0.18, 0);
        this.headGroup.add(neckRing);

        this.robotGroup.add(this.headGroup);

        // ================= 2. TORSO & CHEST =================
        this.torsoGroup = new THREE.Group();
        this.torsoGroup.position.set(0, 1.22, 0);

        // Upper Chest Armor Plate
        const chestGeo = new THREE.BoxGeometry(0.66, 0.44, 0.35);
        const chest = new THREE.Mesh(chestGeo, armorMat);
        chest.position.set(0, 0.14, 0);
        this.torsoGroup.add(chest);

        // Collar Mantle
        const collarGeo = new THREE.BoxGeometry(0.48, 0.08, 0.38);
        const collar = new THREE.Mesh(collarGeo, darkMetalMat);
        collar.position.set(0, 0.34, 0);
        this.torsoGroup.add(collar);

        // Glowing Nexora Arc Reactor (Chest Logo)
        const reactorOuterGeo = new THREE.TorusGeometry(0.1, 0.022, 16, 32);
        const reactorOuter = new THREE.Mesh(reactorOuterGeo, darkMetalMat);
        reactorOuter.position.set(0, 0.14, 0.18);
        this.torsoGroup.add(reactorOuter);

        const reactorCoreGeo = new THREE.CircleGeometry(0.085, 32);
        this.reactorCore = new THREE.Mesh(reactorCoreGeo, cyanGlowMat);
        this.reactorCore.position.set(0, 0.14, 0.19);
        this.torsoGroup.add(this.reactorCore);

        // Stylized "N" Insignia inside Arc Reactor
        const nSymbolGeo = new THREE.BoxGeometry(0.018, 0.08, 0.01);
        const nLeft = new THREE.Mesh(nSymbolGeo, darkMetalMat);
        nLeft.position.set(-0.03, 0.14, 0.20);
        this.torsoGroup.add(nLeft);

        const nRight = new THREE.Mesh(nSymbolGeo, darkMetalMat);
        nRight.position.set(0.03, 0.14, 0.20);
        this.torsoGroup.add(nRight);

        const nDiagGeo = new THREE.BoxGeometry(0.018, 0.1, 0.01);
        const nDiag = new THREE.Mesh(nDiagGeo, darkMetalMat);
        nDiag.rotation.z = -0.55;
        nDiag.position.set(0, 0.14, 0.20);
        this.torsoGroup.add(nDiag);

        // Abdominal Hydraulic Spine
        const spineGeo = new THREE.CylinderGeometry(0.16, 0.2, 0.32, 16);
        const spine = new THREE.Mesh(spineGeo, darkMetalMat);
        spine.position.set(0, -0.2, 0);
        this.torsoGroup.add(spine);

        // Pelvis & Hip Anchor Block
        const pelvisGeo = new THREE.BoxGeometry(0.48, 0.2, 0.28);
        const pelvis = new THREE.Mesh(pelvisGeo, armorMat);
        pelvis.position.set(0, -0.4, 0);
        this.torsoGroup.add(pelvis);

        const pelvicLEDGeo = new THREE.BoxGeometry(0.3, 0.015, 0.01);
        const pelvicLED = new THREE.Mesh(pelvicLEDGeo, cyanGlowMat);
        pelvicLED.position.set(0, -0.4, 0.145);
        this.torsoGroup.add(pelvicLED);

        this.robotGroup.add(this.torsoGroup);

        // ================= 3. SHOULDERS, ARMS & HANDS =================
        // Right Arm (Articulated for waving, gesturing, thinking)
        this.rightArmGroup = new THREE.Group();
        this.rightArmGroup.position.set(0.44, 1.42, 0);

        const shoulderGeo = new THREE.SphereGeometry(0.13, 20, 20);
        const rightShoulder = new THREE.Mesh(shoulderGeo, armorMat);
        this.rightArmGroup.add(rightShoulder);

        const bicepGeo = new THREE.CylinderGeometry(0.065, 0.075, 0.3, 16);
        const rightBicep = new THREE.Mesh(bicepGeo, darkMetalMat);
        rightBicep.position.set(0.02, -0.19, 0);
        this.rightArmGroup.add(rightBicep);

        this.rightForearm = new THREE.Group();
        this.rightForearm.position.set(0.02, -0.36, 0);

        const forearmGeo = new THREE.CylinderGeometry(0.06, 0.07, 0.3, 16);
        const rightForearmMesh = new THREE.Mesh(forearmGeo, armorMat);
        this.rightForearm.add(rightForearmMesh);

        // Right Hand with fingers
        const handGeo = new THREE.BoxGeometry(0.075, 0.11, 0.045);
        this.rightHand = new THREE.Mesh(handGeo, chromeMat);
        this.rightHand.position.set(0, -0.2, 0);
        this.rightForearm.add(this.rightHand);

        this.rightArmGroup.add(this.rightForearm);
        this.robotGroup.add(this.rightArmGroup);

        // Left Arm
        this.leftArmGroup = new THREE.Group();
        this.leftArmGroup.position.set(-0.44, 1.42, 0);

        const leftShoulder = new THREE.Mesh(shoulderGeo, armorMat);
        this.leftArmGroup.add(leftShoulder);

        const leftBicep = new THREE.Mesh(bicepGeo, darkMetalMat);
        leftBicep.position.set(-0.02, -0.19, 0);
        this.leftArmGroup.add(leftBicep);

        this.leftForearm = new THREE.Group();
        this.leftForearm.position.set(-0.02, -0.36, 0);

        const leftForearmMesh = new THREE.Mesh(forearmGeo, armorMat);
        this.leftForearm.add(leftForearmMesh);

        const leftHand = new THREE.Mesh(handGeo, chromeMat);
        leftHand.position.set(0, -0.2, 0);
        this.leftForearm.add(leftHand);

        this.leftArmGroup.add(this.leftForearm);
        this.robotGroup.add(this.leftArmGroup);

        // ================= 4. LEGS & FEET (MANDATORY HUMANOID ANATOMY) =================
        this.legsGroup = new THREE.Group();
        this.legsGroup.position.set(0, 0.72, 0);

        // Right Leg
        this.rightLeg = new THREE.Group();
        this.rightLeg.position.set(0.16, 0, 0);

        // Right Hip Joint
        const hipJointGeo = new THREE.SphereGeometry(0.075, 16, 16);
        const rightHip = new THREE.Mesh(hipJointGeo, chromeMat);
        this.rightLeg.add(rightHip);

        // Right Thigh (Upper Leg)
        const thighGeo = new THREE.CylinderGeometry(0.07, 0.08, 0.42, 16);
        const rightThighMesh = new THREE.Mesh(thighGeo, armorMat);
        rightThighMesh.position.set(0, -0.22, 0);
        this.rightLeg.add(rightThighMesh);

        // Right Knee Joint with Cyan LED Ring
        const kneeGeo = new THREE.SphereGeometry(0.07, 16, 16);
        const rightKnee = new THREE.Mesh(kneeGeo, darkMetalMat);
        rightKnee.position.set(0, -0.45, 0.01);
        this.rightLeg.add(rightKnee);

        const kneeLEDGeo = new THREE.TorusGeometry(0.072, 0.01, 12, 24);
        const rightKneeLED = new THREE.Mesh(kneeLEDGeo, cyanGlowMat);
        rightKneeLED.position.set(0, -0.45, 0.02);
        this.rightLeg.add(rightKneeLED);

        // Right Shin / Lower Leg
        this.rightLowerLeg = new THREE.Group();
        this.rightLowerLeg.position.set(0, -0.45, 0);

        const shinGeo = new THREE.CylinderGeometry(0.062, 0.075, 0.42, 16);
        const rightShinMesh = new THREE.Mesh(shinGeo, armorMat);
        rightShinMesh.position.set(0, -0.23, 0);
        this.rightLowerLeg.add(rightShinMesh);

        // Right Foot (Magnetic Boot with Glowing Hover Sole)
        const footGeo = new THREE.BoxGeometry(0.11, 0.07, 0.22);
        const rightFoot = new THREE.Mesh(footGeo, darkMetalMat);
        rightFoot.position.set(0, -0.46, 0.04);
        this.rightLowerLeg.add(rightFoot);

        const soleGlowGeo = new THREE.BoxGeometry(0.09, 0.01, 0.18);
        const rightSoleGlow = new THREE.Mesh(soleGlowGeo, cyanGlowMat);
        rightSoleGlow.position.set(0, -0.5, 0.04);
        this.rightLowerLeg.add(rightSoleGlow);

        this.rightLeg.add(this.rightLowerLeg);
        this.legsGroup.add(this.rightLeg);

        // Left Leg
        this.leftLeg = new THREE.Group();
        this.leftLeg.position.set(-0.16, 0, 0);

        const leftHip = new THREE.Mesh(hipJointGeo, chromeMat);
        this.leftLeg.add(leftHip);

        const leftThighMesh = new THREE.Mesh(thighGeo, armorMat);
        leftThighMesh.position.set(0, -0.22, 0);
        this.leftLeg.add(leftThighMesh);

        const leftKnee = new THREE.Mesh(kneeGeo, darkMetalMat);
        leftKnee.position.set(0, -0.45, 0.01);
        this.leftLeg.add(leftKnee);

        const leftKneeLED = new THREE.Mesh(kneeLEDGeo, cyanGlowMat);
        leftKneeLED.position.set(0, -0.45, 0.02);
        this.leftLeg.add(leftKneeLED);

        this.leftLowerLeg = new THREE.Group();
        this.leftLowerLeg.position.set(0, -0.45, 0);

        const leftShinMesh = new THREE.Mesh(shinGeo, armorMat);
        leftShinMesh.position.set(0, -0.23, 0);
        this.leftLowerLeg.add(leftShinMesh);

        const leftFoot = new THREE.Mesh(footGeo, darkMetalMat);
        leftFoot.position.set(0, -0.46, 0.04);
        this.leftLowerLeg.add(leftFoot);

        const leftSoleGlow = new THREE.Mesh(soleGlowGeo, cyanGlowMat);
        leftSoleGlow.position.set(0, -0.5, 0.04);
        this.leftLowerLeg.add(leftSoleGlow);

        this.leftLeg.add(this.leftLowerLeg);
        this.legsGroup.add(this.leftLeg);

        this.robotGroup.add(this.legsGroup);

        // ================= 5. DUAL HOLOGRAPHIC PROCESSING RINGS =================
        this.processingRingsGroup = new THREE.Group();
        this.processingRingsGroup.position.set(0, 1.25, 0);

        const ring1Geo = new THREE.TorusGeometry(0.75, 0.015, 16, 64);
        this.ring1 = new THREE.Mesh(ring1Geo, cyanGlowMat);
        this.processingRingsGroup.add(this.ring1);

        const ring2Geo = new THREE.TorusGeometry(0.85, 0.015, 16, 64);
        this.ring2 = new THREE.Mesh(ring2Geo, purpleGlowMat);
        this.ring2.rotation.x = Math.PI / 3;
        this.processingRingsGroup.add(this.ring2);

        this.processingRingsGroup.visible = false;
        this.robotGroup.add(this.processingRingsGroup);
    }

    buildHoverPlatform() {
        this.platformGroup = new THREE.Group();
        this.platformGroup.position.set(0, -0.25, 0);

        // Hexagonal Holographic Wireframe Grid
        const gridGeo = new THREE.CircleGeometry(1.35, 6);
        const gridMat = new THREE.MeshBasicMaterial({
            color: 0x00f2fe,
            wireframe: true,
            transparent: true,
            opacity: 0.28
        });
        const grid = new THREE.Mesh(gridGeo, gridMat);
        grid.rotation.x = -Math.PI / 2;
        this.platformGroup.add(grid);

        // Inner Rotating Cybernetic Ring
        const ringGeo1 = new THREE.RingGeometry(0.85, 0.95, 32);
        const ringMat1 = new THREE.MeshBasicMaterial({
            color: 0x00f2fe,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.65
        });
        this.platformInnerRing = new THREE.Mesh(ringGeo1, ringMat1);
        this.platformInnerRing.rotation.x = -Math.PI / 2;
        this.platformGroup.add(this.platformInnerRing);

        // Outer Rotating Energy Ring
        const ringGeo2 = new THREE.RingGeometry(1.15, 1.22, 32);
        const ringMat2 = new THREE.MeshBasicMaterial({
            color: 0xa855f7,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.5
        });
        this.platformOuterRing = new THREE.Mesh(ringGeo2, ringMat2);
        this.platformOuterRing.rotation.x = -Math.PI / 2;
        this.platformGroup.add(this.platformOuterRing);

        this.scene.add(this.platformGroup);
    }

    buildHolographicField() {
        const particleCount = 75;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);

        for (let i = 0; i < particleCount * 3; i += 3) {
            positions[i] = (Math.random() - 0.5) * 3.0;
            positions[i + 1] = Math.random() * 2.6 - 0.2;
            positions[i + 2] = (Math.random() - 0.5) * 3.0;
        }

        geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
        const material = new THREE.PointsMaterial({
            color: 0x00f2fe,
            size: 0.035,
            transparent: true,
            opacity: 0.55,
            blending: THREE.AdditiveBlending
        });

        this.particleSystem = new THREE.Points(geometry, material);
        this.scene.add(this.particleSystem);
    }

    setState(newState, speechMessage = null) {
        this.state = newState;
        console.log(`[Nexora 3D Robot] State changed to: ${newState}`);

        // Update status pill badge in navbar
        const statusPill = document.getElementById("robot-status-pill");
        if (statusPill) {
            statusPill.textContent = newState.toUpperCase();
            statusPill.className = `status-pill status-${newState}`;
        }

        // Update Speech Bubble
        const bubble = document.getElementById("robot-speech-bubble");
        if (bubble) {
            if (speechMessage) {
                bubble.textContent = speechMessage;
                bubble.style.opacity = "1";
            } else if (newState === "thinking") {
                bubble.textContent = "Analyzing multimodal query...";
                bubble.style.opacity = "1";
            } else if (newState === "listening") {
                bubble.textContent = "Listening carefully...";
                bubble.style.opacity = "1";
            } else if (newState === "greeting") {
                bubble.textContent = "Hello! I am your Nexora AI assistant.";
                bubble.style.opacity = "1";
            } else if (newState === "processing") {
                bubble.textContent = "Synthesizing generative visual output...";
                bubble.style.opacity = "1";
            } else if (newState === "speaking") {
                bubble.textContent = "Sharing my response...";
                bubble.style.opacity = "1";
            } else {
                bubble.textContent = "Online & listening. How can I assist you?";
                bubble.style.opacity = "1";
            }
        }

        // Color adjustments based on state
        if (newState === "thinking") {
            this.leftEye.material.color.setHex(0xa855f7); // Violet contemplation
            this.rightEye.material.color.setHex(0xa855f7);
            this.coreLight.color.setHex(0xa855f7);
            this.processingRingsGroup.visible = true;
        } else if (newState === "listening") {
            this.leftEye.material.color.setHex(0x10b981); // Emerald attention
            this.rightEye.material.color.setHex(0x10b981);
            this.coreLight.color.setHex(0x10b981);
            this.processingRingsGroup.visible = false;
        } else if (newState === "speaking") {
            this.leftEye.material.color.setHex(0x00f2fe);
            this.rightEye.material.color.setHex(0x00f2fe);
            this.coreLight.color.setHex(0x00f2fe);
            this.processingRingsGroup.visible = false;
        } else if (newState === "processing") {
            this.leftEye.material.color.setHex(0x00f2fe);
            this.rightEye.material.color.setHex(0x00f2fe);
            this.processingRingsGroup.visible = true;
        } else {
            this.leftEye.material.color.setHex(0x00f2fe);
            this.rightEye.material.color.setHex(0x00f2fe);
            this.coreLight.color.setHex(0x00f2fe);
            this.processingRingsGroup.visible = false;
        }
    }

    onMouseMove(event) {
        if (!this.container) return;
        const rect = this.container.getBoundingClientRect();
        const clientX = event.clientX - rect.left;
        const clientY = event.clientY - rect.top;

        this.mouse.targetX = (clientX / (rect.width || 450)) * 2 - 1;
        this.mouse.targetY = -(clientY / (rect.height || 750)) * 2 + 1;
    }

    onWindowResize() {
        if (!this.container || !this.renderer || !this.camera) return;
        const width = this.container.clientWidth || 450;
        const height = this.container.clientHeight || 750;

        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        const delta = this.clock.getDelta();
        const elapsed = this.clock.getElapsedTime();

        // Mouse look-around dampening
        this.mouse.x += (this.mouse.targetX - this.mouse.x) * 0.05;
        this.mouse.y += (this.mouse.targetY - this.mouse.y) * 0.05;

        // Platform rotations
        if (this.platformInnerRing) this.platformInnerRing.rotation.z += delta * 0.35;
        if (this.platformOuterRing) this.platformOuterRing.rotation.z -= delta * 0.22;

        // Floating particles
        if (this.particleSystem) {
            this.particleSystem.rotation.y = elapsed * 0.025;
        }

        // Base Idle Floating Levitation
        const hoverY = Math.sin(elapsed * 1.5) * 0.06;
        this.robotGroup.position.y = hoverY;

        // Breathing chest motion
        const breathe = 1.0 + Math.sin(elapsed * 2.0) * 0.015;
        this.torsoGroup.scale.set(breathe, breathe, breathe);

        // Core light pulsation
        this.coreLight.intensity = 2.0 + Math.sin(elapsed * 3.0) * 0.6;

        // ================= STATE MACHINE ANIMATIONS =================
        if (this.state === "idle") {
            // Natural slight look-around
            this.headGroup.rotation.y = this.mouse.x * 0.32 + Math.sin(elapsed * 0.8) * 0.06;
            this.headGroup.rotation.x = -this.mouse.y * 0.22;
            this.headGroup.rotation.z = Math.sin(elapsed * 1.2) * 0.02;

            // Rested natural arms
            this.rightArmGroup.rotation.z = -0.12 + Math.sin(elapsed * 1.5) * 0.02;
            this.rightArmGroup.rotation.x = 0;
            this.rightForearm.rotation.x = -0.15;

            this.leftArmGroup.rotation.z = 0.12 - Math.sin(elapsed * 1.5) * 0.02;
            this.leftArmGroup.rotation.x = 0;
            this.leftForearm.rotation.x = -0.15;

            this.mouthMesh.scale.x = 1.0;

            // Subtle leg balance
            this.rightLeg.rotation.x = Math.sin(elapsed * 1.5) * 0.02;
            this.leftLeg.rotation.x = -Math.sin(elapsed * 1.5) * 0.02;
        }
        else if (this.state === "greeting") {
            // Friendly right hand wave
            this.headGroup.rotation.y = 0.12;
            this.headGroup.rotation.z = 0.06;

            this.rightArmGroup.rotation.z = 0.95;
            this.rightArmGroup.rotation.x = 0.35;
            this.rightForearm.rotation.z = 0.45 + Math.sin(elapsed * 7.5) * 0.35; // Energetic friendly wave
            this.rightForearm.rotation.x = -0.2;

            this.leftArmGroup.rotation.z = 0.18;
        }
        else if (this.state === "thinking") {
            // Head tilted up with contemplation
            this.headGroup.rotation.y = 0.22;
            this.headGroup.rotation.x = 0.22 + Math.sin(elapsed * 2.0) * 0.04;
            this.headGroup.rotation.z = -0.1;

            // Hand to chin gesture
            this.rightArmGroup.rotation.z = 0.32;
            this.rightArmGroup.rotation.x = 0.82;
            this.rightForearm.rotation.x = -1.25;

            if (this.processingRingsGroup.visible) {
                this.ring1.rotation.x += delta * 2.5;
                this.ring1.rotation.y += delta * 1.8;
                this.ring2.rotation.y -= delta * 2.2;
            }
        }
        else if (this.state === "listening") {
            // Forward attentive posture
            this.headGroup.rotation.y = this.mouse.x * 0.4;
            this.headGroup.rotation.x = -0.18;
            this.torsoGroup.rotation.x = 0.08;

            this.rightArmGroup.rotation.z = -0.22;
            this.leftArmGroup.rotation.z = 0.22;

            // Expanded ocular pulse
            const pulse = 1.0 + Math.sin(elapsed * 6.0) * 0.18;
            this.eyesGroup.scale.set(pulse, pulse, 1);
        }
        else if (this.state === "speaking") {
            // Rhythmic speech gesturing & subtle head nodding
            this.headGroup.rotation.y = this.mouse.x * 0.28 + Math.sin(elapsed * 3.5) * 0.08;
            this.headGroup.rotation.x = Math.sin(elapsed * 4.0) * 0.07;
            this.headGroup.rotation.z = Math.sin(elapsed * 2.0) * 0.03;

            // Expressive communicative arm gestures
            this.rightArmGroup.rotation.x = 0.3 + Math.sin(elapsed * 2.5) * 0.18;
            this.rightArmGroup.rotation.z = -0.2 + Math.sin(elapsed * 2.0) * 0.12;
            this.rightForearm.rotation.x = -0.5 + Math.sin(elapsed * 3.0) * 0.22;

            this.leftArmGroup.rotation.x = 0.1 + Math.sin(elapsed * 2.0) * 0.10;
            this.leftArmGroup.rotation.z = 0.15;

            // Mouth visualizer dynamic speech amplitude
            this.mouthMesh.scale.x = 1.0 + Math.abs(Math.sin(elapsed * 12.0)) * 1.8;
            this.mouthMesh.scale.y = 1.0 + Math.abs(Math.sin(elapsed * 14.0)) * 2.2;

            // Synchronized chest arc-reactor and ocular pulsation
            this.coreLight.intensity = 2.4 + Math.abs(Math.sin(elapsed * 10.0)) * 1.2;
            const speechPulse = 1.0 + Math.abs(Math.sin(elapsed * 8.0)) * 0.12;
            this.eyesGroup.scale.set(speechPulse, speechPulse, 1);
        }
        else if (this.state === "processing") {
            // High speed generative state
            this.headGroup.rotation.y = Math.sin(elapsed * 1.5) * 0.2;
            this.headGroup.rotation.x = 0;

            if (this.processingRingsGroup.visible) {
                this.ring1.rotation.x += delta * 4.0;
                this.ring1.rotation.z += delta * 3.0;
                this.ring2.rotation.y += delta * 3.5;
            }
        }

        this.renderer.render(this.scene, this.camera);
    }
}

// Global Exports
window.NexoraRobot = NexoraRobot;

window.initNexoraRobot = function(containerId) {
    if (!window.nexoraRobotInstance) {
        window.nexoraRobotInstance = new NexoraRobot(containerId || "robot-canvas-container");
    }
    return window.nexoraRobotInstance;
};
