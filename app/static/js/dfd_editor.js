"use strict";
/**
 * DFD Editor - Interactive Data Flow Diagram Builder
 * Features: drag-and-drop, selection, label editing, deletion,
 * proper DFD notation shapes, element-to-element connections, undo/redo.
 */

(function () {
  // ─── State ───────────────────────────────────────────────────────────
  let elements = [];
  let connections = [];
  let canvas = null;
  let ctx = null;

  // Interaction state
  let selectedId = null;
  let dragging = false;
  let dragOffsetX = 0;
  let dragOffsetY = 0;
  let connecting = false;
  let connectFromId = null;
  let connectPreview = null;
  let idCounter = 1;

  // Undo/Redo
  let undoStack = [];
  let redoStack = [];
  const MAX_UNDO = 50;

  // ─── Constants ───────────────────────────────────────────────────────
  const GRID_SIZE = 10;
  const COLORS = {
    process: '#3498db',
    datastore: '#2ecc71',
    external: '#e67e22',
    trustBoundary: '#9b59b6',
    flow: '#e74c3c',
    selected: '#f1c40f',
    canvas_bg: '#1e293b',
    grid: 'rgba(100,116,139,0.1)',
    text: '#ffffff'
  };

  const DEFAULTS = {
    process: { w: 120, h: 60, label: 'Process' },
    datastore: { w: 130, h: 50, label: 'Data Store' },
    external: { w: 110, h: 60, label: 'External Entity' },
    trustBoundary: { w: 200, h: 150, label: 'Trust Boundary' }
  };

  // ─── Initialization ──────────────────────────────────────────────────
  function initializeCanvas() {
    canvas = document.getElementById('dfdCanvas');
    if (!canvas) {
      console.error('Canvas element not found');
      return false;
    }
    ctx = canvas.getContext('2d');
    resizeCanvas();
    bindEvents();
    bindToolbarEvents();
    drawAll();
    return true;
  }

  function resizeCanvas() {
    const container = canvas.parentElement;
    canvas.width = container.clientWidth || 900;
    canvas.height = 550;
  }

  // ─── Event Binding ───────────────────────────────────────────────────
  function bindEvents() {
    canvas.addEventListener('mousedown', onMouseDown);
    canvas.addEventListener('mousemove', onMouseMove);
    canvas.addEventListener('mouseup', onMouseUp);
    canvas.addEventListener('dblclick', onDoubleClick);
    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('resize', function () {
      resizeCanvas();
      drawAll();
    });
  }

  // ─── Toolbar Event Delegation ──────────────────────────────────────────
  function bindToolbarEvents() {
    var toolbar = document.querySelector('.dfd-toolbar');
    if (!toolbar) return;

    toolbar.addEventListener('click', function(e) {
      var button = e.target.closest('[data-action]');
      if (!button) return;

      var action = button.getAttribute('data-action');
      switch (action) {
        case 'add-element':
          addElement(button.getAttribute('data-element-type'));
          break;
        case 'start-connection':
          startConnection();
          break;
        case 'delete-selected':
          deleteSelected();
          break;
        case 'undo':
          undo();
          break;
        case 'redo':
          redo();
          break;
        case 'clear-all':
          clearAll();
          break;
        case 'save-canvas':
          saveCanvas();
          break;
      }
    });
  }

  // ─── Mouse Handlers ──────────────────────────────────────────────────
  function getMousePos(e) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };
  }

  function hitTest(x, y) {
    // Iterate in reverse so top-most element is selected first
    for (let i = elements.length - 1; i >= 0; i--) {
      const el = elements[i];
      if (x >= el.x && x <= el.x + el.w && y >= el.y && y <= el.y + el.h) {
        return el;
      }
    }
    return null;
  }

  function onMouseDown(e) {
    const pos = getMousePos(e);
    const hit = hitTest(pos.x, pos.y);

    if (connecting) {
      if (hit && hit.id !== connectFromId) {
        // Complete connection
        saveState();
        connections.push({
          from: connectFromId,
          to: hit.id,
          label: 'Data Flow'
        });
        connecting = false;
        connectFromId = null;
        connectPreview = null;
        canvas.style.cursor = 'default';
        drawAll();
      }
      return;
    }

    if (hit) {
      selectedId = hit.id;
      dragging = true;
      dragOffsetX = pos.x - hit.x;
      dragOffsetY = pos.y - hit.y;
      canvas.style.cursor = 'grabbing';
    } else {
      selectedId = null;
      // Check if clicked on a connection label
      const conn = hitTestConnection(pos.x, pos.y);
      if (conn) {
        selectedId = 'conn_' + connections.indexOf(conn);
      }
    }
    drawAll();
  }

  function onMouseMove(e) {
    const pos = getMousePos(e);

    if (connecting) {
      connectPreview = pos;
      drawAll();
      return;
    }

    if (dragging && selectedId) {
      const el = getElementById(selectedId);
      if (el) {
        el.x = snap(pos.x - dragOffsetX);
        el.y = snap(pos.y - dragOffsetY);
        // Keep within canvas bounds
        el.x = Math.max(0, Math.min(canvas.width - el.w, el.x));
        el.y = Math.max(0, Math.min(canvas.height - el.h, el.y));
        drawAll();
      }
    } else {
      // Hover cursor
      const hit = hitTest(pos.x, pos.y);
      canvas.style.cursor = hit ? 'grab' : 'default';
    }
  }

  function onMouseUp(e) {
    if (dragging) {
      saveState();
      dragging = false;
      canvas.style.cursor = 'grab';
    }
  }

  function onDoubleClick(e) {
    const pos = getMousePos(e);
    const hit = hitTest(pos.x, pos.y);

    if (hit) {
      const newLabel = prompt('Enter label:', hit.label);
      if (newLabel !== null && newLabel.trim() !== '') {
        saveState();
        hit.label = newLabel.trim();
        drawAll();
      }
      return;
    }

    // Check connection label
    const conn = hitTestConnection(pos.x, pos.y);
    if (conn) {
      const newLabel = prompt('Enter flow label:', conn.label);
      if (newLabel !== null && newLabel.trim() !== '') {
        saveState();
        conn.label = newLabel.trim();
        drawAll();
      }
    }
  }

  function onKeyDown(e) {
    // Delete selected element
    if ((e.key === 'Delete' || e.key === 'Backspace') && selectedId) {
      if (document.activeElement && document.activeElement.tagName === 'INPUT') return;
      e.preventDefault();
      deleteSelected();
    }
    // Undo: Ctrl+Z
    if (e.ctrlKey && e.key === 'z') {
      e.preventDefault();
      undo();
    }
    // Redo: Ctrl+Y or Ctrl+Shift+Z
    if (e.ctrlKey && (e.key === 'y' || (e.shiftKey && e.key === 'Z'))) {
      e.preventDefault();
      redo();
    }
    // Escape: cancel connection mode
    if (e.key === 'Escape') {
      if (connecting) {
        connecting = false;
        connectFromId = null;
        connectPreview = null;
        canvas.style.cursor = 'default';
        drawAll();
      }
      selectedId = null;
      drawAll();
    }
  }

  // ─── Connection Hit Test ─────────────────────────────────────────────
  function hitTestConnection(x, y) {
    for (let i = 0; i < connections.length; i++) {
      const conn = connections[i];
      const fromEl = getElementById(conn.from);
      const toEl = getElementById(conn.to);
      if (!fromEl || !toEl) continue;

      const midX = (fromEl.x + fromEl.w / 2 + toEl.x + toEl.w / 2) / 2;
      const midY = (fromEl.y + fromEl.h / 2 + toEl.y + toEl.h / 2) / 2;

      if (Math.abs(x - midX) < 40 && Math.abs(y - midY) < 15) {
        return conn;
      }
    }
    return null;
  }

  // ─── Drawing ─────────────────────────────────────────────────────────
  function drawAll() {
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Background
    ctx.fillStyle = COLORS.canvas_bg;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Grid
    drawGrid();

    // Draw trust boundaries first (behind everything)
    elements.filter(function (el) { return el.type === 'trustBoundary'; }).forEach(drawElement);

    // Draw connections
    connections.forEach(drawConnection);

    // Draw connection preview
    if (connecting && connectPreview && connectFromId) {
      const fromEl = getElementById(connectFromId);
      if (fromEl) {
        ctx.setLineDash([6, 4]);
        ctx.strokeStyle = COLORS.flow;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(fromEl.x + fromEl.w / 2, fromEl.y + fromEl.h / 2);
        ctx.lineTo(connectPreview.x, connectPreview.y);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    }

    // Draw elements (except trust boundaries)
    elements.filter(function (el) { return el.type !== 'trustBoundary'; }).forEach(drawElement);
  }

  function drawGrid() {
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 0.5;
    for (let x = 0; x < canvas.width; x += GRID_SIZE * 2) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += GRID_SIZE * 2) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }
  }

  function drawElement(el) {
    var isSelected = (el.id === selectedId);

    ctx.save();

    if (el.type === 'process') {
      drawProcess(el, isSelected);
    } else if (el.type === 'datastore') {
      drawDataStore(el, isSelected);
    } else if (el.type === 'external') {
      drawExternalEntity(el, isSelected);
    } else if (el.type === 'trustBoundary') {
      drawTrustBoundary(el, isSelected);
    }

    ctx.restore();
  }

  function drawProcess(el, isSelected) {
    var cx = el.x + el.w / 2;
    var cy = el.y + el.h / 2;
    var rx = el.w / 2;
    var ry = el.h / 2;

    // Shadow
    ctx.shadowColor = 'rgba(0,0,0,0.3)';
    ctx.shadowBlur = 8;
    ctx.shadowOffsetY = 3;

    // Ellipse (proper DFD process shape)
    ctx.beginPath();
    ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
    ctx.fillStyle = COLORS.process;
    ctx.fill();

    ctx.shadowBlur = 0;
    ctx.shadowOffsetY = 0;

    // Border
    ctx.strokeStyle = isSelected ? COLORS.selected : '#2980b9';
    ctx.lineWidth = isSelected ? 3 : 2;
    ctx.stroke();

    // Label
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 12px Manrope, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    wrapText(ctx, el.label, cx, cy, el.w - 20, 14);
  }

  function drawDataStore(el, isSelected) {
    // Data store: two parallel horizontal lines (open-ended rectangle)
    ctx.shadowColor = 'rgba(0,0,0,0.3)';
    ctx.shadowBlur = 8;
    ctx.shadowOffsetY = 3;

    // Fill area
    ctx.fillStyle = COLORS.datastore;
    ctx.fillRect(el.x, el.y, el.w, el.h);

    ctx.shadowBlur = 0;
    ctx.shadowOffsetY = 0;

    // Top and bottom lines (DFD notation)
    ctx.strokeStyle = isSelected ? COLORS.selected : '#27ae60';
    ctx.lineWidth = isSelected ? 3 : 2;
    ctx.beginPath();
    ctx.moveTo(el.x, el.y);
    ctx.lineTo(el.x + el.w, el.y);
    ctx.moveTo(el.x, el.y + el.h);
    ctx.lineTo(el.x + el.w, el.y + el.h);
    ctx.stroke();

    // Left divider line
    ctx.beginPath();
    ctx.moveTo(el.x + 20, el.y);
    ctx.lineTo(el.x + 20, el.y + el.h);
    ctx.stroke();

    // Label
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 12px Manrope, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    wrapText(ctx, el.label, el.x + 20 + (el.w - 20) / 2, el.y + el.h / 2, el.w - 30, 14);
  }

  function drawExternalEntity(el, isSelected) {
    // External entity: rectangle (square box)
    ctx.shadowColor = 'rgba(0,0,0,0.3)';
    ctx.shadowBlur = 8;
    ctx.shadowOffsetY = 3;

    ctx.fillStyle = COLORS.external;
    ctx.fillRect(el.x, el.y, el.w, el.h);

    ctx.shadowBlur = 0;
    ctx.shadowOffsetY = 0;

    ctx.strokeStyle = isSelected ? COLORS.selected : '#d35400';
    ctx.lineWidth = isSelected ? 3 : 2;
    ctx.strokeRect(el.x, el.y, el.w, el.h);

    // Label
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 12px Manrope, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    wrapText(ctx, el.label, el.x + el.w / 2, el.y + el.h / 2, el.w - 16, 14);
  }

  function drawTrustBoundary(el, isSelected) {
    // Trust boundary: dashed rectangle
    ctx.setLineDash([8, 5]);
    ctx.strokeStyle = isSelected ? COLORS.selected : COLORS.trustBoundary;
    ctx.lineWidth = isSelected ? 3 : 2;
    ctx.strokeRect(el.x, el.y, el.w, el.h);
    ctx.setLineDash([]);

    // Label at top
    ctx.fillStyle = COLORS.trustBoundary;
    ctx.font = 'bold 11px Manrope, sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'bottom';
    ctx.fillText(el.label, el.x + 8, el.y - 4);
  }

  function drawConnection(conn) {
    var fromEl = getElementById(conn.from);
    var toEl = getElementById(conn.to);
    if (!fromEl || !toEl) return;

    var from = getConnectionPoint(fromEl, toEl);
    var to = getConnectionPoint(toEl, fromEl);

    var isSelected = (selectedId === 'conn_' + connections.indexOf(conn));

    // Line
    ctx.strokeStyle = isSelected ? COLORS.selected : COLORS.flow;
    ctx.lineWidth = isSelected ? 3 : 2;
    ctx.beginPath();
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(to.x, to.y);
    ctx.stroke();

    // Arrowhead
    var angle = Math.atan2(to.y - from.y, to.x - from.x);
    var headLen = 12;
    ctx.fillStyle = isSelected ? COLORS.selected : COLORS.flow;
    ctx.beginPath();
    ctx.moveTo(to.x, to.y);
    ctx.lineTo(to.x - headLen * Math.cos(angle - Math.PI / 6),
      to.y - headLen * Math.sin(angle - Math.PI / 6));
    ctx.lineTo(to.x - headLen * Math.cos(angle + Math.PI / 6),
      to.y - headLen * Math.sin(angle + Math.PI / 6));
    ctx.closePath();
    ctx.fill();

    // Label at midpoint
    if (conn.label) {
      var midX = (from.x + to.x) / 2;
      var midY = (from.y + to.y) / 2;

      ctx.fillStyle = 'rgba(30,41,59,0.85)';
      var textWidth = ctx.measureText(conn.label).width;
      ctx.fillRect(midX - textWidth / 2 - 6, midY - 10, textWidth + 12, 20);

      ctx.fillStyle = '#f1f5f9';
      ctx.font = '11px Manrope, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(conn.label, midX, midY);
    }
  }

  function getConnectionPoint(fromEl, toEl) {
    // Get the edge point of fromEl closest to toEl center
    var fx = fromEl.x + fromEl.w / 2;
    var fy = fromEl.y + fromEl.h / 2;
    var tx = toEl.x + toEl.w / 2;
    var ty = toEl.y + toEl.h / 2;

    var angle = Math.atan2(ty - fy, tx - fx);

    if (fromEl.type === 'process') {
      // Ellipse edge
      var rx = fromEl.w / 2;
      var ry = fromEl.h / 2;
      var cos = Math.cos(angle);
      var sin = Math.sin(angle);
      var denom = Math.sqrt((ry * cos) * (ry * cos) + (rx * sin) * (rx * sin));
      return {
        x: fx + (rx * ry * cos) / denom,
        y: fy + (rx * ry * sin) / denom
      };
    } else {
      // Rectangle edge
      var hw = fromEl.w / 2;
      var hh = fromEl.h / 2;
      var absCos = Math.abs(Math.cos(angle));
      var absSin = Math.abs(Math.sin(angle));
      var d;
      if (hw * absSin <= hh * absCos) {
        d = hw / absCos;
      } else {
        d = hh / absSin;
      }
      return {
        x: fx + d * Math.cos(angle),
        y: fy + d * Math.sin(angle)
      };
    }
  }

  // ─── Text Wrapping ───────────────────────────────────────────────────
  function wrapText(context, text, x, y, maxWidth, lineHeight) {
    var words = text.split(' ');
    var lines = [];
    var currentLine = words[0] || '';

    for (var i = 1; i < words.length; i++) {
      var testLine = currentLine + ' ' + words[i];
      if (context.measureText(testLine).width > maxWidth) {
        lines.push(currentLine);
        currentLine = words[i];
      } else {
        currentLine = testLine;
      }
    }
    lines.push(currentLine);

    var startY = y - ((lines.length - 1) * lineHeight) / 2;
    for (var j = 0; j < lines.length; j++) {
      context.fillText(lines[j], x, startY + j * lineHeight);
    }
  }

  // ─── Helpers ─────────────────────────────────────────────────────────
  function getElementById(id) {
    for (var i = 0; i < elements.length; i++) {
      if (elements[i].id === id) return elements[i];
    }
    return null;
  }

  function snap(val) {
    return Math.round(val / GRID_SIZE) * GRID_SIZE;
  }

  function generateId() {
    return 'el_' + (idCounter++);
  }

  // ─── Undo/Redo ──────────────────────────────────────────────────────
  function saveState() {
    undoStack.push(JSON.stringify({ elements: elements, connections: connections }));
    if (undoStack.length > MAX_UNDO) undoStack.shift();
    redoStack = [];
  }

  function undo() {
    if (undoStack.length === 0) return;
    redoStack.push(JSON.stringify({ elements: elements, connections: connections }));
    var state = JSON.parse(undoStack.pop());
    elements = state.elements;
    connections = state.connections;
    selectedId = null;
    recalcIdCounter();
    drawAll();
  }

  function redo() {
    if (redoStack.length === 0) return;
    undoStack.push(JSON.stringify({ elements: elements, connections: connections }));
    var state = JSON.parse(redoStack.pop());
    elements = state.elements;
    connections = state.connections;
    selectedId = null;
    recalcIdCounter();
    drawAll();
  }

  function recalcIdCounter() {
    var max = 0;
    elements.forEach(function (el) {
      var num = parseInt((el.id || '').replace('el_', ''), 10);
      if (num > max) max = num;
    });
    idCounter = max + 1;
  }

  // ─── Public API (called from HTML buttons) ───────────────────────────
  function addElement(type) {
    if (!ctx && !initializeCanvas()) {
      alert('Error: Canvas not available.');
      return;
    }

    saveState();

    var def = DEFAULTS[type];
    var el = {
      id: generateId(),
      type: type,
      x: snap(80 + Math.random() * (canvas.width - 250)),
      y: snap(60 + Math.random() * (canvas.height - 200)),
      w: def.w,
      h: def.h,
      label: def.label
    };

    elements.push(el);
    selectedId = el.id;
    drawAll();
  }

  function startConnection() {
    if (!selectedId || selectedId.startsWith('conn_')) {
      alert('Select an element first, then click "Add Flow".');
      return;
    }
    connecting = true;
    connectFromId = selectedId;
    canvas.style.cursor = 'crosshair';
  }

  function deleteSelected() {
    if (!selectedId) return;

    saveState();

    if (selectedId.startsWith('conn_')) {
      var idx = parseInt(selectedId.replace('conn_', ''), 10);
      connections.splice(idx, 1);
    } else {
      // Remove element and its connections
      elements = elements.filter(function (el) { return el.id !== selectedId; });
      connections = connections.filter(function (c) {
        return c.from !== selectedId && c.to !== selectedId;
      });
    }

    selectedId = null;
    drawAll();
  }

  function clearAll() {
    if (!confirm('Clear entire diagram? This cannot be undone.')) return;
    saveState();
    elements = [];
    connections = [];
    selectedId = null;
    drawAll();
  }

  function saveCanvas() {
    if (!window.dfdSaveUrl) {
      alert('Save URL is not configured.');
      return;
    }

    var csrfToken = document.querySelector('meta[name="csrf-token"]');
    csrfToken = csrfToken ? csrfToken.getAttribute('content') : '';

    var payload = JSON.stringify({
      elements: elements,
      connections: connections,
      idCounter: idCounter
    });

    fetch(window.dfdSaveUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({ canvas_json: payload })
    })
      .then(function (res) {
        if (!res.ok) throw new Error('Save failed: ' + res.status);
        return res.json();
      })
      .then(function (data) {
        if (data.status === 'saved') {
          showToast('DFD saved successfully!', 'success');
        } else {
          showToast('Unable to save DFD.', 'danger');
        }
      })
      .catch(function (err) {
        console.error(err);
        showToast('Error saving DFD: ' + err.message, 'danger');
      });
  }

  function loadFromJSON(jsonStr) {
    if (!jsonStr || jsonStr === '{}' || jsonStr === '[]') return;
    try {
      var data = JSON.parse(jsonStr);
      if (Array.isArray(data)) {
        // Legacy format (old array of elements)
        elements = data.map(function (el, i) {
          if (!el.id) el.id = 'el_' + (i + 1);
          return el;
        });
        connections = [];
      } else if (data.elements) {
        // New format
        elements = data.elements || [];
        connections = data.connections || [];
        if (data.idCounter) idCounter = data.idCounter;
      }
      recalcIdCounter();
      drawAll();
    } catch (e) {
      console.error('Error loading DFD data:', e);
    }
  }

  function showToast(message, type) {
    // Simple toast notification
    var toast = document.createElement('div');
    toast.className = 'alert alert-' + (type || 'info') + ' position-fixed';
    toast.style.cssText = 'top:20px;right:20px;z-index:9999;min-width:250px;animation:slideIn 0.3s ease;';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(function () {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s';
      setTimeout(function () { toast.remove(); }, 300);
    }, 2500);
  }

  // ─── Expose to global scope ──────────────────────────────────────────
  window.dfdEditor = {
    init: initializeCanvas,
    addElement: addElement,
    startConnection: startConnection,
    deleteSelected: deleteSelected,
    clearAll: clearAll,
    saveCanvas: saveCanvas,
    loadFromJSON: loadFromJSON,
    undo: undo,
    redo: redo
  };

  // Legacy global functions for backward compatibility
  window.initializeCanvas = initializeCanvas;
  window.addElement = addElement;
  window.saveCanvas = saveCanvas;

})();
