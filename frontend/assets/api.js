/* =========================================================================
   api.js —— 用 window.EZGYM_API 渲染 API 文档：
   左侧域导航、端点卡片（可展开）、顶部搜索过滤、滚动高亮当前域。
   零依赖原生 JS。
   ========================================================================= */
(function () {
  'use strict';

  var DATA = window.EZGYM_API;
  if (!DATA) return;

  /* ---------- 工具 ---------- */
  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  // 轻量语法高亮：作用在已转义文本上（引号未被转义，仍是 "）
  function hl(escaped) {
    return escaped
      .replace(/(&quot;|")([^"]*?)("|&quot;)/g, '<span class="str">$1$2$3</span>')
      .replace(/\b(true|false|null)\b/g, '<span class="bool">$1</span>')
      .replace(/(:\s*)(-?\d+(?:\.\d+)?)/g, '$1<span class="num">$2</span>');
  }
  function el(html) {
    var t = document.createElement('template');
    t.innerHTML = html.trim();
    return t.content.firstElementChild;
  }
  // 路径中的 {var} 高亮
  function pathHtml(p) {
    return esc(p).replace(/\{([^}]+)\}/g, '<span class="var">{$1}</span>');
  }

  var AUTH_LABEL = {
    public: ['公开', 'public'],
    soft: ['软登录', 'soft'],
    login: ['登录', 'login'],
    admin: ['管理员', 'admin']
  };

  /* ---------- 渲染单个端点 ---------- */
  function renderEndpoint(ep) {
    var m = ep.method.toLowerCase();
    var auth = AUTH_LABEL[ep.auth] || ['公开', 'public'];

    var params = (ep.params && ep.params.length)
      ? '<ul class="params">' + ep.params.map(function (p) {
        return '<li>' +
          '<span class="pn">' + esc(p.n) + '</span>' +
          '<span class="pt">' + esc(p.t) + '</span>' +
          '<span class="pt">· ' + esc(p.in) + '</span>' +
          (p.req ? '<span class="preq">required</span>' : '') +
          '<span class="pd">' + esc(p.d) + '</span>' +
        '</li>';
      }).join('') + '</ul>'
      : '<p class="params__none">无参数</p>';

    var reqBlock = ep.reqBody
      ? '<span class="cap">示例请求体</span><pre>' + hl(esc(ep.reqBody)) + '</pre>'
      : '<span class="cap">请求</span><pre>' + hl(esc(ep.method + ' ' + ep.path)) + '</pre>';

    var crBadge = ep.cr ? ' <span class="cr">✱ ' + esc(ep.cr) + '</span>' : '';

    var searchText = (ep.method + ' ' + ep.path + ' ' + ep.desc + ' ' + (ep.cr || '')).toLowerCase();

    var node = el(
      '<details class="ep" data-search="' + esc(searchText) + '">' +
        '<summary class="ep__summary">' +
          '<span class="method method--' + m + '">' + esc(ep.method) + '</span>' +
          '<span class="ep__path">' + pathHtml(ep.path) + '</span>' +
          '<span class="ep__auth ep__auth--' + auth[1] + '">' + auth[0] + '</span>' +
          '<svg class="ep__chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>' +
        '</summary>' +
        '<div class="ep__body">' +
          '<p class="ep__desc">' + esc(ep.desc) + crBadge + '</p>' +
          '<div class="ep__grid">' +
            '<div class="ep__col">' +
              '<h5>请求参数</h5>' + params +
              '<div class="code" style="margin-top:14px">' + reqBlock + '</div>' +
            '</div>' +
            '<div class="ep__col">' +
              '<h5>响应契约 · {errno, code, data}</h5>' +
              '<div class="code"><span class="cap">示例响应</span><pre>' + hl(esc(ep.res)) + '</pre></div>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</details>'
    );
    return node;
  }

  /* ---------- 渲染域块 + 导航 ---------- */
  var main = document.getElementById('doc-main');
  var nav = document.getElementById('doc-nav');
  var totalEndpoints = 0;

  DATA.domains.forEach(function (d) {
    totalEndpoints += d.endpoints.length;

    // 导航项
    var navItem = el(
      '<li><a href="#' + d.id + '" data-target="' + d.id + '">' +
        '<span class="n">' + d.no + '</span>' + d.name +
        '<span class="c">' + d.endpoints.length + '</span>' +
      '</a></li>'
    );
    nav.appendChild(navItem);

    // 域块
    var block = el(
      '<section class="domain-block" id="' + d.id + '">' +
        '<div class="domain-block__head">' +
          '<span class="n">' + d.no + '</span>' +
          '<h2>' + esc(d.name) + '</h2>' +
          '<span class="zh">' + esc(d.zh) + (d.support ? ' · support' : '') + '</span>' +
        '</div>' +
        '<p class="domain-block__desc">' + esc(d.desc) + '</p>' +
      '</section>'
    );
    d.endpoints.forEach(function (ep) { block.appendChild(renderEndpoint(ep)); });
    main.appendChild(block);
  });

  // 端点计数
  var countEl = document.getElementById('doc-count');
  if (countEl) countEl.textContent = DATA.domains.length + ' 域 · ' + totalEndpoints + ' 端点';
  var chipEl = document.getElementById('endpoint-total');
  if (chipEl) chipEl.textContent = totalEndpoints;

  /* ---------- 搜索过滤 ---------- */
  var search = document.getElementById('doc-search-input');
  var noResult = document.getElementById('doc-no-result');
  if (search) {
    search.addEventListener('input', function () {
      var q = search.value.trim().toLowerCase();
      var anyVisible = false;
      DATA.domains.forEach(function (d) {
        var block = document.getElementById(d.id);
        var eps = block.querySelectorAll('.ep');
        var visibleInBlock = 0;
        eps.forEach(function (epEl) {
          var match = !q || epEl.getAttribute('data-search').indexOf(q) !== -1;
          epEl.style.display = match ? '' : 'none';
          if (match) { visibleInBlock++; anyVisible = true; }
          // 有查询时自动展开匹配项，便于阅读
          if (q && match) { epEl.setAttribute('open', ''); }
          else if (q) { epEl.removeAttribute('open'); }
        });
        block.style.display = visibleInBlock ? '' : 'none';
      });
      if (noResult) noResult.classList.toggle('hidden', anyVisible);
    });
  }

  /* ---------- 滚动高亮当前域 ---------- */
  var navLinks = Array.prototype.slice.call(nav.querySelectorAll('a'));
  function setActive(id) {
    navLinks.forEach(function (a) {
      a.classList.toggle('is-active', a.getAttribute('data-target') === id);
    });
  }
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) setActive(e.target.id);
      });
    }, { rootMargin: '-30% 0px -60% 0px', threshold: 0 });
    DATA.domains.forEach(function (d) {
      var b = document.getElementById(d.id);
      if (b) io.observe(b);
    });
  }
  if (DATA.domains[0]) setActive(DATA.domains[0].id);
})();
