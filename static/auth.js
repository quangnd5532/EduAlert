'use strict';
document.querySelectorAll('[data-password-target]').forEach(button => {
  button.addEventListener('click', () => {
    const input = document.getElementById(button.dataset.passwordTarget);
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    button.setAttribute('aria-pressed', String(show));
    button.setAttribute('aria-label', show ? 'Ẩn mật khẩu' : 'Hiện mật khẩu');
  });
});
document.querySelectorAll('form[data-loading-label]').forEach(form => {
  form.addEventListener('submit', () => {
    const button = form.querySelector('button[type="submit"]');
    if (!button) return;
    button.disabled = true;
    button.setAttribute('aria-busy', 'true');
    button.dataset.originalContent = button.innerHTML;
    button.textContent = form.dataset.loadingLabel;
  });
});
window.addEventListener('pageshow', () => {
  document.querySelectorAll('button[data-original-content]').forEach(button => {
    button.innerHTML = button.dataset.originalContent;
    button.disabled = false;
    button.removeAttribute('aria-busy');
  });
});
const resend = document.querySelector('[data-resend-countdown]');
if (resend) {
  const until = Date.now() + Number(resend.dataset.resendCountdown) * 1000;
  const refresh = () => {
    const remaining = Math.max(0, Math.ceil((until - Date.now()) / 1000));
    resend.disabled = remaining > 0;
    resend.textContent = remaining ? `Gửi lại mã (${remaining}s)` : 'Gửi lại mã';
    return remaining;
  };
  if (refresh()) {
    const timer = setInterval(() => { if (!refresh()) clearInterval(timer); }, 1000);
  }
}
document.querySelectorAll('a[href="#account-support"]').forEach(link => {
  link.addEventListener('click', () => {
    const support = document.getElementById('account-support');
    support.open = true;
    support.querySelector('summary').focus();
  });
});
