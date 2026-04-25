document.addEventListener('DOMContentLoaded', function () {
  var toggleButton = document.getElementById('sidebar-toggle-btn');
  var sidebarElement = document.getElementById('sidebar');

  if (!toggleButton || !sidebarElement || !window.coreui || !window.coreui.Sidebar) {
    return;
  }

  toggleButton.addEventListener('click', function () {
    var sidebar = window.coreui.Sidebar.getOrCreateInstance(sidebarElement);
    sidebar.toggle();
  });
});
