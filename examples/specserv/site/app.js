document.addEventListener('keydown', function (ev) {
  if (ev.key === '/' && document.activeElement.tagName !== 'INPUT') {
    var input = document.querySelector('.search-form input[name="q"]');
    if (input) {
      ev.preventDefault();
      input.focus();
    }
  }
});
