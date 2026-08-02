/* ============================================================================
 * src/js/coverageFilter.js
 *
 * "Is my area covered?" search over the ~456 localities on /locate-us/.
 *
 * A list this long is unreadable without a way in — the whole point of the
 * page is answering one question, and scrolling five cities of sector numbers
 * is not an answer. Typing "62" should settle it in a second.
 *
 * The search box ships `hidden` and is only revealed here: with no JS the
 * list is still complete and readable, but a search box that does nothing
 * would not be.
 *
 * Matching is substring on the locality name. "Sector 6" deliberately also
 * matches "Sector 62" — someone checking coverage wants to see the whole
 * neighbourhood, not one exact string.
 * ========================================================================== */

let teardown = null;

const norm = (s) => (s || '').toLowerCase().trim();

export function initCoverageFilter() {
  if (teardown) teardown();
  if (typeof document === 'undefined') return (teardown = () => {});

  const finder = document.querySelector('[data-coverage-finder]');
  if (!finder) return (teardown = () => {});

  const input = finder.querySelector('[data-coverage-search]');
  const clear = finder.querySelector('[data-coverage-clear]');
  const count = finder.querySelector('[data-coverage-count]');
  const empty = document.querySelector('[data-coverage-empty]');
  const cities = Array.from(document.querySelectorAll('[data-coverage-city]'));
  const cols = Array.from(document.querySelectorAll('[data-coverage-col]'));
  const items = Array.from(document.querySelectorAll('[data-coverage-item]'));
  if (!input || !items.length) return (teardown = () => {});

  // Read each name once instead of touching the DOM 456 times per keystroke.
  const index = items.map((el) => ({ el, text: norm(el.getAttribute('data-name')) }));

  finder.hidden = false;

  const apply = () => {
    const q = norm(input.value);
    let shown = 0;

    index.forEach(({ el, text }) => {
      const hit = !q || text.includes(q);
      el.hidden = !hit;
      if (hit) shown++;
    });

    // Collapse empty columns, then empty cities — otherwise a search leaves a
    // page of headings with nothing under them.
    cols.forEach((col) => {
      const any = Array.from(col.querySelectorAll('[data-coverage-item]')).some((i) => !i.hidden);
      col.hidden = !!q && !any;
    });
    cities.forEach((city) => {
      const any = Array.from(city.querySelectorAll('[data-coverage-item]')).some((i) => !i.hidden);
      city.hidden = !!q && !any;
    });

    clear.hidden = !q;
    if (empty) empty.hidden = !(q && shown === 0);

    if (!q) {
      count.textContent = '';
    } else if (shown === 0) {
      count.textContent = 'No match for “' + input.value.trim() + '”.';
    } else {
      count.textContent =
        shown === 1
          ? '1 area matches “' + input.value.trim() + '” — yes, we collect there.'
          : shown + ' areas match “' + input.value.trim() + '” — yes, we collect there.';
    }
  };

  const onInput = () => apply();
  const onClear = () => {
    input.value = '';
    apply();
    input.focus();
  };
  const onKey = (e) => {
    if (e.key === 'Escape' && input.value) {
      e.preventDefault();
      onClear();
    }
  };

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
