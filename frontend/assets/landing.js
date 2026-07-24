/* =========================================================================
   landing.js —— 落地页轻交互：
   1) BURN GAUGE 燃烧刻度条：进入视口后填充到目标值
   2) 滚动出现动画（.reveal → .in）
   3) 导航当前锚点高亮
   全部尊重 prefers-reduced-motion。
   ========================================================================= */
(function () {
  'use strict';
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 1. BURN GAUGE ---------- */
  var gauge = document.querySelector('[data-gauge]');
  if (gauge) {
    var target = parseFloat(gauge.getAttribute('data-gauge')) || 0; // 0~100
    var fill = gauge.querySelector('.gauge__fill');
    var needle = gauge.querySelector('.gauge__needle');
    var value = gauge.querySelector('[data-gauge-value]');
    var to = Math.max(0, Math.min(100, target));

    function paint(pct) {
      if (fill) fill.style.width = pct + '%';
      if (needle) needle.style.left = pct + '%';
    }
    function run() {
      if (reduce) {
        paint(to);
        if (value) value.firstChild.textContent = Math.round(to * 4.9); // 展示卡路里读数
        return;
      }
      paint(to);
      // 数字滚动
      if (value) {
        var start = null, dur = 1400, endN = Math.round(to * 4.9);
        function step(ts) {
          if (!start) start = ts;
          var p = Math.min(1, (ts - start) / dur);
          var eased = 1 - Math.pow(1 - p, 3);
          value.firstChild.textContent = Math.round(endN * eased);
          if (p < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
      }
    }
    if ('IntersectionObserver' in window) {
      var go = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { run(); go.disconnect(); }
        });
      }, { threshold: 0.3 });
      go.observe(gauge);
    } else { run(); }
  }

  /* ---------- 2. 滚动出现 ---------- */
  var reveals = document.querySelectorAll('.reveal');
  if (reveals.length && !reduce && 'IntersectionObserver' in window) {
    var ro = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); ro.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });
    reveals.forEach(function (n) { ro.observe(n); });
  } else {
    reveals.forEach(function (n) { n.classList.add('in'); });
  }

  /* ---------- 3. 导航高亮 ---------- */
  var links = Array.prototype.slice.call(document.querySelectorAll('.nav a[data-target]'));
  var sections = links
    .map(function (a) { return document.getElementById(a.getAttribute('data-target')); })
    .filter(Boolean);
  if (sections.length && 'IntersectionObserver' in window) {
    var so = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          links.forEach(function (a) {
            a.classList.toggle('is-active', a.getAttribute('data-target') === e.target.id);
          });
        }
      });
    }, { rootMargin: '-40% 0px -55% 0px' });
    sections.forEach(function (s) { so.observe(s); });
  }
})();
