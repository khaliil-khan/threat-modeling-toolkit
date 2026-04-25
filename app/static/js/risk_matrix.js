function drawRiskMatrix(canvasId, threats) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const size = 350;
    const cellSize = size / 5;
    canvas.width = size;
    canvas.height = size;

    // Clear canvas
    ctx.clearRect(0, 0, size, size);

    // Draw 5x5 heatmap grid
    for (let y = 1; y <= 5; y++) {
        for (let x = 1; x <= 5; x++) {
            const riskScore = (x + y) / 2;
            let color;
            if (riskScore >= 4.5) color = '#c0392b';
            else if (riskScore >= 3.5) color = '#e67e22';
            else if (riskScore >= 2.5) color = '#f1c40f';
            else color = '#2ecc71';
            ctx.fillStyle = color + '88'; // semi-transparent
            ctx.fillRect((x-1)*cellSize, (5-y)*cellSize, cellSize, cellSize);
            ctx.strokeStyle = '#ddd';
            ctx.strokeRect((x-1)*cellSize, (5-y)*cellSize, cellSize, cellSize);
        }
    }

    // Draw axes labels
    ctx.fillStyle = '#333';
    ctx.font = '12px Arial';
    for (let i = 1; i <= 5; i++) {
        ctx.fillText(i, (i-1)*cellSize + cellSize/3, size - 5);
        ctx.fillText(i, 5, (5-i)*cellSize + cellSize/2);
    }
    ctx.save();
    ctx.translate(20, size/2);
    ctx.rotate(-Math.PI/2);
    ctx.fillText('Damage (Impact)', -40, 10);
    ctx.restore();
    ctx.fillText('Exploitability (Likelihood)', size/2 - 60, size - 8);

    // Plot threat points
    threats.forEach(threat => {
        const x = threat.x;
        const y = threat.y;
        if (x >= 1 && x <= 5 && y >= 1 && y <= 5) {
            const cx = (x - 0.5) * cellSize;
            const cy = (5.5 - y) * cellSize;
            ctx.beginPath();
            ctx.arc(cx, cy, 6, 0, 2 * Math.PI);
            let pointColor = '#2c3e50';
            if (threat.risk_level === 'Critical') pointColor = '#8e44ad';
            else if (threat.risk_level === 'High') pointColor = '#d35400';
            else if (threat.risk_level === 'Medium') pointColor = '#f39c12';
            else pointColor = '#27ae60';
            ctx.fillStyle = pointColor;
            ctx.fill();
        }
    });
}
