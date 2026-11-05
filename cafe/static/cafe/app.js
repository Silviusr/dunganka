document.querySelectorAll('[data-checkout]').forEach(form => {
  form.addEventListener('submit', () => {
    if (!form.checkValidity()) return;
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    button.textContent = 'Открываем WhatsApp…';
  });
});
window.addEventListener('pageshow', () => document.querySelectorAll('[data-checkout] button[type="submit"]').forEach(button => {
  button.disabled = false;
  button.textContent = 'Отправить в WhatsApp ↗';
}));

// Add in place: no navigation, category reset or change to the document height.
const cartFeedback = document.querySelector('[data-cart-feedback]');
let feedbackTimer;
let cartBusy = false;
function showCartFeedback(message, error = false) {
  clearTimeout(feedbackTimer);
  cartFeedback.textContent = message;
  cartFeedback.classList.toggle('is-error', error);
  cartFeedback.hidden = false;
  feedbackTimer = setTimeout(() => { cartFeedback.hidden = true; }, 6000);
}
document.querySelectorAll('[data-cart-add]').forEach(form => {
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (cartBusy) return;
    cartBusy = true;
    const buttons = document.querySelectorAll('[data-cart-add] button');
    buttons.forEach(button => { button.disabled = true; });
    try {
      const response = await fetch(form.action, {
        method: 'POST', body: new FormData(form),
        headers: { 'Accept': 'application/json' }, credentials: 'same-origin',
      });
      const data = await response.json();
      if (typeof data.cart_count === 'number') {
        document.querySelectorAll('[data-cart-count]').forEach(counter => {
          counter.textContent = data.cart_count;
        });
      }
      showCartFeedback(data.message, !response.ok || !data.ok);
    } catch {
      // Do not retry a POST: the server may already have added the item.
      showCartFeedback('Не удалось получить подтверждение. Проверьте корзину перед повторным добавлением.', true);
    } finally {
      cartBusy = false;
      buttons.forEach(button => { button.disabled = false; });
    }
  });
});
