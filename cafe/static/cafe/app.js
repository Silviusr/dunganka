document.querySelectorAll('[data-checkout]').forEach(form => {
  form.addEventListener('submit', () => {
    if (!form.checkValidity()) return;
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    button.textContent = 'Сохраняем…';
  });
});
window.addEventListener('pageshow', () => document.querySelectorAll('[data-checkout] button[type="submit"]').forEach(button => {
  button.disabled = false;
  button.textContent = 'Сохранить демозаявку ↗';
}));
