// Draw 5x5 risk matrix heatmap with threat points
function drawRiskMatrix(canvasId, threats) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const size = 350;
    const cellSize = size / 5; // 70px per cell
    canvas.width = size;
    canvas.height = size;
    
    // Clear
    ctx.clearRect(0, 0, size, size);
    
    // Draw grid and background colors based on risk score (x+y)/2
    for (let y = 1; y <= 5; y++) {
        for (let x = 1; x <= 5; x++) {
            const riskScore = (x + y) / 2;
            let color;
            if (riskScore >= 4.5) color = '#c0392b';      // Critical - dark red
            else if (riskScore >= 3.5) color = '#e67e22'; // High - orange
            else if (riskScore >= 2.5) color = '#f1c40f'; // Medium - yellow
            else color = '#2ecc71';                       // Low - green
            
            ctx.fillStyle = color + '88'; // semi-transparent
            ctx.fillRect((x-1)*cellSize, (5-y)*cellSize, cellSize, cellSize);
            ctx.strokeStyle = '#ddd';
            ctx.strokeRect((x-1)*cellSize, (5-y)*cellSize, cellSize, cellSize);
        }
    }
    
    // Draw axis labels
    ctx.fillStyle = '#333';
    ctx.font = '12px Arial';
    for (let i = 1; i <= 5; i++) {
        // X axis (exploitability)
        ctx.fillText(i, (i-1)*cellSize + cellSize/3, size - 5);
        // Y axis (damage)
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
        const x = threat.x;      // exploitability 1-5
        const y = threat.y;      // damage 1-5
        if (x >= 1 && x <= 5 && y >= 1 && y <= 5) {
            const cx = (x - 0.5) * cellSize;
            const cy = (5.5 - y) * cellSize;
            ctx.beginPath();
            ctx.arc(cx, cy, 6, 0, 2 * Math.PI);
            // Color based on risk level
            let pointColor = '#2c3e50';
            if (threat.risk_level === 'Critical') pointColor = '#8e44ad';
            else if (threat.risk_level === 'High') pointColor = '#d35400';
            else if (threat.risk_level === 'Medium') pointColor = '#f39c12';
            else pointColor = '#27ae60';
            ctx.fillStyle = pointColor;
            ctx.fill();
            ctx.fillStyle = 'white';
            ctx.font = 'bold 10px Arial';
            ctx.fillText('●', cx-2, cy+2);
        }
    });
    
    // Add tooltip-like behavior on hover (simplified: just console)
    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const mouseX = (e.clientX - rect.left) * scaleX;
        const mouseY = (e.clientY - rect.top) * scaleY;
        // Find threat near click
        for (let t of threats) {
            const cx = (t.x - 0.5) * cellSize;
            const cy = (5.5 - t.y) * cellSize;
            const dist = Math.hypot(mouseX - cx, mouseY - cy);
            if (dist < 10) {
                canvas.title = `${t.title} (Risk: ${t.risk_level})`;
                break;
            }
        }
    });
}
