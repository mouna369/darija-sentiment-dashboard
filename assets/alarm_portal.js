/*
 * alarm_portal.js — assets/
 * Gère : portail vers <body> + TOUS les boutons de l'alarme
 * Aucun callback Dash utilisé — tout est en JS pur vanilla
 */
(function () {

    var isMuted = false;

    /* ── Attache les handlers sur les boutons ─────────────────── */
    function attachHandlers() {
        var stopBtn = document.getElementById("alarm-stop-btn");
        var dismissBtn = document.getElementById("alarm-dismiss-btn");
        var muteBtn = document.getElementById("alarm-mute-btn");

        if (stopBtn && !stopBtn._alarmBound) { stopBtn._alarmBound = true; stopBtn.addEventListener("click", stopAlarm); }
        if (dismissBtn && !dismissBtn._alarmBound) { dismissBtn._alarmBound = true; dismissBtn.addEventListener("click", stopAlarm); }
        if (muteBtn && !muteBtn._alarmBound) { muteBtn._alarmBound = true; muteBtn.addEventListener("click", toggleMute); }
    }

    /* ── Arrêter complètement l'alarme ───────────────────────── */
    function stopAlarm() {
        var audio = document.getElementById("alarm-audio");
        var overlay = document.getElementById("alarm-overlay");
        if (audio) { audio.pause(); audio.currentTime = 0; }
        if (overlay) { overlay.style.display = "none"; }
    }

    /* ── Couper / réactiver le son ────────────────────────────── */
    function toggleMute() {
        isMuted = !isMuted;
        var audio = document.getElementById("alarm-audio");
        var waves = document.getElementById("alarm-sound-waves");
        var label = document.getElementById("alarm-sound-label");
        var muteBtn = document.getElementById("alarm-mute-btn");

        if (isMuted) {
            if (audio) { audio.muted = true; }
            if (waves) { waves.classList.add("muted"); }
            if (label) { label.textContent = "🔇 Son coupé"; label.classList.add("muted"); }
            if (muteBtn) { muteBtn.textContent = "🔊 Réactiver"; }
        } else {
            if (audio) { audio.muted = false; audio.play().catch(function () { }); }
            if (waves) { waves.classList.remove("muted"); }
            if (label) { label.textContent = "🔊 ALARME ACTIVE"; label.classList.remove("muted"); }
            if (muteBtn) { muteBtn.textContent = "🔇 Couper le son"; }
        }
    }

    /* ── Démarrer l'audio (déblocage navigateur) ─────────────── */
    function startAudio() {
        var audio = document.getElementById("alarm-audio");
        if (audio && audio.paused && !isMuted) {
            audio.volume = 0.8;
            audio.play().catch(function (e) {
                /* Autoplay bloqué — se débloque au premier clic utilisateur */
                document.addEventListener("click", function unblock() {
                    audio.play().catch(function () { });
                    document.removeEventListener("click", unblock);
                }, { once: true });
            });
        }
    }

    /* ── Téléporter le wrapper dans <body> ───────────────────── */
    function moveToBody() {
        var wrapper = document.getElementById("alarm-modal-wrapper");
        if (!wrapper) return;

        /* Déjà dans body et déjà traité */
        if (wrapper.parentElement === document.body && wrapper._alarmInit) return;

        if (wrapper.parentElement !== document.body) {
            document.body.appendChild(wrapper);
        }

        wrapper._alarmInit = true;
        attachHandlers();
        startAudio();
    }

    /* ── Observer les mutations Dash (re-renders) ────────────── */
    var observer = new MutationObserver(function () {
        /* Dash peut recréer les boutons lors d'un re-render :
           on réinitialise les flags et réattache */
        var stopBtn = document.getElementById("alarm-stop-btn");
        var dismissBtn = document.getElementById("alarm-dismiss-btn");
        var muteBtn = document.getElementById("alarm-mute-btn");

        if (stopBtn) stopBtn._alarmBound = false;
        if (dismissBtn) dismissBtn._alarmBound = false;
        if (muteBtn) muteBtn._alarmBound = false;

        moveToBody();
    });

    observer.observe(document.body, { childList: true, subtree: true });

    /* ── Init au chargement ──────────────────────────────────── */
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", moveToBody);
    } else {
        moveToBody();
    }

})();