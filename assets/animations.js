// Animation des cercles de progression
document.addEventListener('DOMContentLoaded', function () {
    // Attendre un peu que Plotly soit chargé
    setTimeout(function () {
        animateAllRings();
    }, 200);
});

function animateAllRings() {
    // Trouver tous les conteneurs de cercles
    var rings = document.querySelectorAll('[data-target-pct]');

    rings.forEach(function (container) {
        var targetPct = parseInt(container.getAttribute('data-target-pct'));
        var targetScore = parseFloat(container.getAttribute('data-target-score'));
        var color = container.getAttribute('data-color');
        var graphId = container.getAttribute('data-id');

        if (graphId) {
            animateRing(graphId, targetPct, targetScore, color);
        }
    });
}

function animateRing(graphId, targetPct, finalScore, color) {
    var graphElement = document.getElementById(graphId);
    if (!graphElement) return;

    var startPct = 0;
    var duration = 1000; // 1 seconde
    var startTime = null;

    function updateRing(currentPct) {
        // Mettre à jour les valeurs du graphique Plotly
        Plotly.restyle(graphId, {
            'values': [[currentPct, 100 - currentPct]]
        }, 1); // L'index 1 correspond au deuxième trace (l'anneau coloré)

        // Mettre à jour le texte si nécessaire
        var currentScore = (currentPct / 100) * 2 - 1;
        var scoreText = currentScore.toFixed(2);
        if (currentScore >= 0) scoreText = '+' + scoreText;

        Plotly.relayout(graphId, {
            'annotations[0].text': scoreText,
            'annotations[0].font.color': color
        });
    }

    function animate(timestamp) {
        if (!startTime) startTime = timestamp;
        var elapsed = timestamp - startTime;
        var progress = Math.min(1, elapsed / duration);

        var currentPct = Math.floor(startPct + (targetPct - startPct) * progress);
        updateRing(currentPct);

        if (progress < 1) {
            requestAnimationFrame(animate);
        } else {
            // Animation terminée, afficher la valeur finale
            updateRing(targetPct);
        }
    }

    requestAnimationFrame(animate);
}