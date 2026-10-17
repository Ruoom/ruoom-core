(function () {
  if (window.ruoomEmbeddedSignin) return;
  window.ruoomEmbeddedSignin = true;

  async function load(container, url, form) {
    if (container.dataset.loading) return;
    container.dataset.loading = 'true';
    container.setAttribute('aria-busy', 'true');
    var buttons = container.querySelectorAll('button[type="submit"]');
    buttons.forEach(function (button) { button.disabled = true; });
    try {
      var options = {
        credentials: 'same-origin',
        headers: {'X-Ruoom-Embedded-Signin': '1'}
      };
      if (form) {
        options.method = 'POST';
        options.body = new FormData(form);
      }
      var response = await fetch(url, options);
      if (response.headers.get('Content-Type').includes('application/json')) {
        var result = await response.json();
        if (result.authenticated || result.redirect_url) {
          var target = new URL(result.redirect_url || window.location.href, window.location.href);
          if (target.origin !== window.location.origin) throw new Error('Invalid redirect');
          window.location.assign(target.href);
          return;
        }
        throw new Error('Unexpected response');
      }
      var html = await response.text();
      // Do not insert a full page if middleware or an unsupported view redirected.
      if (!html.includes('data-embedded-signin-form') || /<html|<body/i.test(html)) {
        throw new Error('Unexpected sign-in response');
      }
      container.innerHTML = html;
      var field = container.querySelector('[autofocus], input:not([type="hidden"])');
      if (field) field.focus();
    } catch (error) {
      var message = container.querySelector('[data-signin-network-error]');
      if (!message) {
        message = document.createElement('p');
        message.dataset.signinNetworkError = '';
        message.className = 'alert alert-danger';
        message.setAttribute('role', 'alert');
        container.prepend(message);
      }
      message.textContent = container.dataset.errorMessage || 'Unable to sign in right now. Please try again.';
    } finally {
      delete container.dataset.loading;
      container.removeAttribute('aria-busy');
      buttons.forEach(function (button) { button.disabled = false; });
    }
  }

  document.addEventListener('click', function (event) {
    var link = event.target.closest('[data-embedded-signin-link]');
    var container = link && link.closest('[data-embedded-signin]');
    if (!container || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    load(container, link.href);
  });
  document.addEventListener('submit', function (event) {
    var form = event.target.closest('[data-embedded-signin-form]');
    var container = form && form.closest('[data-embedded-signin]');
    if (!container) return;
    event.preventDefault();
    load(container, form.action, form);
  });
})();
