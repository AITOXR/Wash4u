/* ============================================================================
 * src/js/svcFilter.js
 *
 * "What do you need cleaned?" — filters the service grid on /services/.
 *
 * The guide asks for a service filter, and on a 15-card grid it earns its
 * place: people arrive knowing the ITEM ("saree", "sneakers", "carpet"), not
 * the service name. Each card is indexed on its name, slug and "best for"
 * line, so typing an item finds the service that handles it.
 *
 * Ships `hidden` and revealed here — with no JS the grid is complete and a
 * dead search box would be worse than none.
 * ========================================================================== */

let teardown = null;
const norm = (s) => (s || '').toLowerCase().trim();

export function initSvcFilter() {
  if (teardown) teardown();
  if (typeof document === 'undefined') return (teardown = () => {});

  const finder = document.querySelector('[data-svc-finder]');
  if (!finder) return (teardown = () => {});

  const input = finder.querySelector('[data-svc-search]');
  const clear = finder.querySelector('[data-svc-clear]');
  const count = finder.querySelector('[data-svc-count]');
  const cards = Array.from(document.querySelectorAll('[data-svc-item]'));
  if (!input || !cards.length) return (teardown = () => {});

  const index = cards.map((el) => ({ el, text: norm(el.getAttribute('data-name')) }));
  finder.hidden = false;

  const apply = () => {
    const q = norm(input.value);
    let shown = 0;
    index.forEach(({ el, text }) => {
      const hit = !q || text.includes(q);
      el.hidden = !hit;
      if (hit) shown++;
    });
    clear.hidden = !q;
    if (!q) {
      count.textContent = '';
    } else if (shown === 0) {
      count.textContent = 'Nothing matches “' + input.value.trim() + '”. Ask us on WhatsApp — we probably still clean it.';
    } else {
      count.textContent =
        shown === 1
          ? '1 service handles that.'
          : shown + ' services handle that.';
    }
  };

  const onInput = () => apply();
  const onClear = () => { input.value = ''; apply(); input.focus(); };
  const onKey = (e) => { if (e.key === 'Escape' && input.value) { e.preventDefault(); onClear(); } };

  input.addEventListener('input', onInput);
  input.addEventListener('keydown', onKey);
  clear.addEventListener('click', onClear);
  apply();

  const cleanup = () => {
    input.removeEventListener('input', onInput);
    input.removeEventListener('keydown', onKey);
    clear.removeEventListener('click', onClear);
    if (teardown === cleanup) teardown = null;
  };
  teardown = cleanup;
  return cleanup;
}
