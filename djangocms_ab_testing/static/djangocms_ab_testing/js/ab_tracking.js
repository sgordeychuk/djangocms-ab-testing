(function () {
  'use strict';

  function getCookie(name) {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
      var cookie = cookies[i].trim();
      if (cookie.indexOf(name + '=') === 0) {
        return cookie.substring(name.length + 1);
      }
    }
    return '';
  }

  function trackAB(testName, variant, action) {
    var meta = {
      screen_width: screen.width,
      screen_height: screen.height,
      viewport_width: window.innerWidth,
      viewport_height: window.innerHeight,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      language: navigator.language,
      touch: 'ontouchstart' in window,
    };
    fetch('/api/ab-event/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify({
        test_name: testName,
        variant: variant,
        action: action,
        meta: meta,
      }),
    }).catch(function () {});
  }

  function initABTracking() {
    var container = document.querySelector('[data-ab-test]');
    if (!container) return;

    var variant = container.dataset.abVariant;
    var testName = container.dataset.abTest;
    if (!variant || !testName) return;

    // Auto-track "view" event when variant is rendered
    trackAB(testName, variant, 'view');

    // Find modals: first inside the AB container, then fall back to all page modals
    var modals = container.querySelectorAll('.modal');
    if (!modals.length) {
      modals = document.querySelectorAll('.modal');
    }
    if (!modals.length) return;

    modals.forEach(function (modal) {
      modal.addEventListener('shown.bs.modal', function () {
        trackAB(testName, variant, 'opened');
      });
      modal.addEventListener('hidden.bs.modal', function () {
        trackAB(testName, variant, 'closed');
      });

      // Track CTA clicks (buttons/links inside modal)
      modal.querySelectorAll('.ab-request-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
          trackAB(testName, variant, 'requested');
        });
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initABTracking);
  } else {
    initABTracking();
  }

  window.initABTracking = initABTracking;
})();
