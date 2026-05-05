let elements = [];
let canvas = null;
let ctx = null;

const shapeDefaults = {
  process: { w: 100, h: 50, color: '#3498db', label: 'Process' },
  datastore: { w: 100, h: 60, color: '#2ecc71', label: 'Data Store' },
  external: { w: 80, h: 50, color: '#e67e22', label: 'External Entity' },
  flow: { color: '#e74c3c', label: 'Flow' }
};

function initializeCanvas() {
  canvas = document.getElementById('dfdCanvas');
  ctx = canvas ? canvas.getContext('2d') : null;
  if (!canvas || !ctx) {
    console.error('Canvas element not found or cannot get 2D context');
    return false;
  }
  return true;
}

function addElement(type) {
  if (!ctx) {
    console.warn('Canvas not initialized. Initializing now...');
    if (!initializeCanvas()) {
      alert('Error: Canvas not available.');
      return;
    }
  }
  
  let newEl;
  if (type === 'flow') {
    newEl = {
      type: 'flow',
      x1: 50 + elements.length * 10,
      y1: 100 + elements.length * 15,
      x2: 200 + elements.length * 10,
      y2: 150 + elements.length * 15,
      label: shapeDefaults.flow.label
    };
  } else {
    newEl = {
      type: type,
      x: 50 + elements.length * 20,
      y: 80 + elements.length * 10,
      w: shapeDefaults[type].w,
      h: shapeDefaults[type].h,
      color: shapeDefaults[type].color,
      label: shapeDefaults[type].label
    };
  }
  elements.push(newEl);
  drawAll();
}

function drawAll() {
  if (!ctx) {
    console.warn('Canvas not initialized. Initializing now...');
    if (!initializeCanvas()) {
      console.error('Cannot draw: Canvas context is null');
      return;
    }
  }
  
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  elements.forEach(el => {
    if (el.type === 'flow') {
      ctx.strokeStyle = el.color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(el.x1, el.y1);
      ctx.lineTo(el.x2, el.y2);
      ctx.stroke();
      let angle = Math.atan2(el.y2 - el.y1, el.x2 - el.x1);
      let headLen = 10;
      ctx.beginPath();
      ctx.moveTo(el.x2, el.y2);
      ctx.lineTo(el.x2 - headLen * Math.cos(angle - Math.PI/6),
                 el.y2 - headLen * Math.sin(angle - Math.PI/6));
      ctx.lineTo(el.x2 - headLen * Math.cos(angle + Math.PI/6),
                 el.y2 - headLen * Math.sin(angle + Math.PI/6));
      ctx.closePath();
      ctx.fillStyle = el.color;
      ctx.fill();
    } else {
      ctx.fillStyle = el.color;
      ctx.fillRect(el.x, el.y, el.w, el.h);
      ctx.strokeStyle = '#2c3e50';
      ctx.strokeRect(el.x, el.y, el.w, el.h);
      ctx.fillStyle = '#fff';
      ctx.font = '12px sans-serif';
      ctx.fillText(el.label, el.x + 5, el.y + 20);
    }
  });
}

function saveCanvas() {
  if (!window.dfdSaveUrl) {
    alert('Save URL is not configured.');
    return;
  }

  // Get CSRF token from meta tag or cookie
  const csrfToken = document.querySelector('meta[name="csrf-token"]')
    ? document.querySelector('meta[name="csrf-token"]').getAttribute('content')
    : '';

  fetch(window.dfdSaveUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({ canvas_json: JSON.stringify(elements) })
  })
  .then(res => {
    if (!res.ok) {
      throw new Error('Save request failed.');
    }
    return res.json();
  })
  .then(data => {
    if (data.status === 'saved') {
      alert('DFD saved!');
    } else {
      alert('Unable to save DFD.');
    }
  })
  .catch(error => {
    console.error(error);
    alert('Unable to save DFD.');
  });
}