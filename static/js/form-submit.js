/* Enviament dels formularis de contacte i contractació.
   Tot el text i la configuració arriben per atributs data-* del <form>,
   perquè la CSP de producció no permet scripts en línia. */
(function () {
  var form = document.querySelector('.booking-form');
  if (!form) return;

  var d = form.dataset || {};
  var status = form.querySelector('.booking-form__status');
  var dest = d.dest || '';
  var type = d.formType || 'contact';
  var subjectPrefix = d.subjectPrefix || '';
  var t = {
    required: d.msgRequired || '',
    email: d.msgEmail || '',
    sending: d.msgSending || '',
    sent: d.msgSent || '',
    error: d.msgError || '',
    mailto: d.msgMailto || ''
  };

  function setError(el, msg) {
    var box = document.getElementById(el.id + '-err');
    if (box) box.textContent = msg || '';
    if (msg) el.setAttribute('aria-invalid', 'true');
    else el.removeAttribute('aria-invalid');
  }

  function mailtoBody() {
    var body = 'Nom: ' + form.elements['name'].value + '\n' +
      'Email: ' + form.elements['email'].value + '\n';
    if (type === 'booking') {
      var org = form.elements['organisation'];
      var date = form.elements['date'];
      body += 'Organització: ' + ((org && org.value) || '-') + '\n' +
        'Data: ' + ((date && date.value) || '-') + '\n';
    }
    return body + '\n' + form.elements['message'].value;
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (form.elements['_hp'] && form.elements['_hp'].value) return;

    var ok = true, firstBad = null;
    [['name', t.required], ['email', t.required], ['message', t.required]].forEach(function (f) {
      var el = form.elements[f[0]];
      if (!el) return;
      var msg = '';
      if (!el.value.trim()) msg = f[1];
      else if (el.type === 'email' && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(el.value.trim())) msg = t.email;
      setError(el, msg);
      if (msg) { ok = false; if (!firstBad) firstBad = el; }
    });
    var consent = form.elements['consent'];
    if (consent && !consent.checked) {
      setError(consent, t.required);
      ok = false;
      if (!firstBad) firstBad = consent;
    }
    if (!ok) { if (firstBad) firstBad.focus(); return; }

    var endpoint = form.getAttribute('data-endpoint');
    var name = form.elements['name'].value;
    var subject = (subjectPrefix ? subjectPrefix + ' — ' : '') + name;

    if (!endpoint) {
      window.location.href = 'mailto:' + dest + '?subject=' +
        encodeURIComponent(subject) + '&body=' + encodeURIComponent(mailtoBody());
      if (status) status.textContent = t.mailto;
      return;
    }

    if (status) status.textContent = t.sending;
    fetch(endpoint, { method: 'POST', body: new FormData(form) })
      .then(function (r) {
        if (!r.ok) throw new Error(r.status);
        form.reset();
        if (status) status.textContent = t.sent;
      })
      .catch(function () {
        if (status) status.textContent = t.error;
        window.location.href = 'mailto:' + dest + '?subject=' +
          encodeURIComponent(subject) + '&body=' + encodeURIComponent(mailtoBody());
      });
  });
})();
