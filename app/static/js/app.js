document.addEventListener('DOMContentLoaded', function() {
  const toggler = document.getElementById('sidebar-toggler');
  if (toggler) {
    toggler.addEventListener('click', function() {
      const sidebar = document.getElementById('sidebar');
      if (sidebar && window.coreui && window.coreui.Sidebar) {
        const sidebarInstance = window.coreui.Sidebar.getOrCreateInstance(sidebar);
        sidebarInstance.toggle();
      }
    });
  }

  const revealTargets = document.querySelectorAll(
    '.container-lg > .alert, .container-lg > .card, .container-lg > section, .container-lg > .row, .container-lg > .py-2, .container-lg > .py-3'
  );

  revealTargets.forEach(function(el, index) {
    el.classList.add('reveal-item');
    el.style.setProperty('--reveal-delay', String(index * 55) + 'ms');
  });

  document.body.classList.add('is-ready');

  const dreadRangeInputs = document.querySelectorAll('input[type="range"]');

  dreadRangeInputs.forEach(function(input) {
    const display = document.querySelector('[data-dread-value-for="' + input.id + '"]');
    if (!display) {
      return;
    }

    const updateValue = function() {
      display.textContent = input.value + '/5';
    };

    input.addEventListener('input', updateValue);
    input.addEventListener('change', updateValue);
    input.addEventListener('touchmove', updateValue, { passive: true });
    updateValue();
  });
});