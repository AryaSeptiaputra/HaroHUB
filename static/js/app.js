// Tutup autocomplete saat klik di luar
document.addEventListener('click', function (e) {
  const dropdown = document.getElementById('search-dropdown');
  if (dropdown && !e.target.closest('#nav-search')) {
    dropdown.innerHTML = '';
  }
});

// Hapus satu query param dari URL saat ini
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

// Reset semua filter
function resetFilters() {
  window.location.href = '/';
}
