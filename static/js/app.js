// ── HTMX: kirim CSRF token otomatis di setiap request ──
document.addEventListener('htmx:configRequest', function (e) {
  const token = document.cookie
    .split('; ')
    .find(r => r.startsWith('csrftoken='))
    ?.split('=')[1];
  if (token) e.detail.headers['X-CSRFToken'] = token;
});

// ── Tutup autocomplete saat klik di luar ──
document.addEventListener('click', function (e) {
  const dropdown = document.getElementById('search-dropdown');
  if (dropdown && !e.target.closest('#nav-search')) {
    dropdown.innerHTML = '';
  }
});

// ── Hapus satu query param dari URL saat ini ──
function removeParam(param, value) {
  const url = new URL(window.location.href);
  if (value !== undefined && value !== null) {
    const values = url.searchParams.getAll(param);
    url.searchParams.delete(param);
    values.filter(v => v !== String(value)).forEach(v => url.searchParams.append(param, v));
  } else {
    url.searchParams.delete(param);
  }
  url.searchParams.delete('page');
  window.location.href = url.href;
}

function resetFilters() {
  window.location.href = '/';
}
