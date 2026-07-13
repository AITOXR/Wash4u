(function () {
  'use strict';

  // Highlight the nav link for the section the visitor is in
  const path = window.location.pathname;
  document.querySelectorAll('.header__link, .mobile-nav__link').forEach(link => {
    const href = link.getAttribute('href');
    if (!href) return;
    const target = href.replace(/^(\.\.\/)+/, '/').replace(/\/+$/, '/');
    if (target !== '/' && path.startsWith(target.startsWith('/') ? target : '/' + target)) {
      link.classList.add('is-active');
    }
  });

  // Sticky header background
  const header = document.getElementById('header');
  function updateHeader() {
    if (window.scrollY > 20) {
      header.classList.add('header--scrolled');
    } else {
      header.classList.remove('header--scrolled');
    }
  }
  window.addEventListener('scroll', updateHeader, { passive: true });
  updateHeader();

  // Mobile nav
  const menuToggle = document.getElementById('menu-toggle');
  const menuClose = document.getElementById('menu-close');
  const mobileNav = document.getElementById('mobile-nav');

  function openMenu() {
    mobileNav.classList.add('is-open');
    mobileNav.setAttribute('aria-hidden', 'false');
    menuToggle.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
  }

  function closeMenu() {
    mobileNav.classList.remove('is-open');
    mobileNav.setAttribute('aria-hidden', 'true');
    menuToggle.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }

  if (menuToggle && mobileNav) {
    menuToggle.addEventListener('click', openMenu);
  }
  if (menuClose && mobileNav) {
    menuClose.addEventListener('click', closeMenu);
  }

  // Service process tabs (Rinse-style 1-2-3)
  document.querySelectorAll('.svc-tabs').forEach(tablist => {
    const container = tablist.parentElement;
    const tabs = tablist.querySelectorAll('.svc-tabs__btn');
    const panels = container.querySelectorAll('.svc-panel');
    tabs.forEach((tab, i) => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => t.setAttribute('aria-selected', 'false'));
        panels.forEach(p => p.classList.remove('is-active'));
        tab.setAttribute('aria-selected', 'true');
        if (panels[i]) panels[i].classList.add('is-active');
      });
    });
  });

  // FAQ accordion
  const faqItems = document.querySelectorAll('.faq-item');
  faqItems.forEach(item => {
    const question = item.querySelector('.faq-item__question');
    question.addEventListener('click', () => {
      const isOpen = item.classList.contains('is-open');
      // Close others
      faqItems.forEach(other => {
        other.classList.remove('is-open');
        other.querySelector('.faq-item__question').setAttribute('aria-expanded', 'false');
      });
      if (!isOpen) {
        item.classList.add('is-open');
        question.setAttribute('aria-expanded', 'true');
      }
    });
  });

  // Scroll reveal
  const revealElements = document.querySelectorAll('.reveal, .stagger-children');
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    revealElements.forEach(el => observer.observe(el));
  } else {
    revealElements.forEach(el => el.classList.add('is-visible'));
  }
})();
