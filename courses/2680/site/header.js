(function () {
  var script = document.currentScript;

  // Resolve the shared header relative to this script's own directory.
  var base = (script.getAttribute('src') || 'header.js').replace(/header\.js.*$/, '');
  var headerUrl = base + 'header.html';

  // Nav links are written from the site root; prefix them so they resolve from
  // the including page's directory depth. The script's own directory is exactly
  // that prefix, for a relative src ('../header.js') and a root-absolute one
  // ('/header.js') alike. 404.html needs the absolute form, because the Worker
  // serves it for unknown paths at any depth.
  var prefix = base;

  var xhr = new XMLHttpRequest();
  xhr.open('GET', headerUrl, false);
  xhr.send(null);
  if (xhr.status < 200 || xhr.status >= 300) return;

  var html = xhr.responseText;
  html = html.replace(/(href|src)="([^"]+)"/g, function (all, attr, url) {
    if (!/^(?:[a-z][a-z0-9]*:|#|\/|data:)/i.test(url)) return attr + '="' + prefix + url + '"';
    return all;
  });

  var holder = document.createElement('div');
  holder.innerHTML = html;

  // Match routes relative to the site root. Local previews often serve this
  // directory below a prefix such as /public/, while production serves it at /.
  var path = location.pathname;
  var scriptPath = new URL(script.src, location.href).pathname;
  var siteRoot = scriptPath.slice(0, scriptPath.lastIndexOf('/') + 1);
  if (path.indexOf(siteRoot) === 0) path = '/' + path.slice(siteRoot.length);

  var role = '';
  if (/^\/assignments(\/|$)/.test(path)) {
    role = 'assignments';
  } else if (/^\/computing(\/|$)/.test(path)) {
    role = 'computing';
  } else {
    var page = (path.split('/').pop() || 'index').replace(/\.html$/, '');
    var roles = {
      '': 'home', 'index': 'home',
      'project': 'project', 'policy': 'policy'
    };
    role = roles[page] || '';
  }

  if (role && holder.querySelectorAll) {
    [].forEach.call(holder.querySelectorAll('[data-role]'), function (a) {
      if (a.getAttribute('data-role') === role) a.classList.add('active');
    });
  }

  var slot = document.getElementById('site-header');
  if (!slot) return;
  var node = holder.firstChild;
  if (slot.replaceWith) slot.replaceWith(node);
  else slot.parentNode.replaceChild(node, slot);
})();
