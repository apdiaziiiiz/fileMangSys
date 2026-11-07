/**
 * Department-Based Document Management System
 * Interactive Prototype Logic (Client-side interactivity & state)
 */

document.addEventListener('DOMContentLoaded', () => {
  initModals();
  initSearchFilter();
  initFolderNavigation();
  initTableSorting();
  initUploadForm();
  initApprovalActions();
  initRoleSwitcher();
});

// Modal Management
function initModals() {
  const openButtons = document.querySelectorAll('[data-modal-target]');
  const closeButtons = document.querySelectorAll('[data-modal-close]');
  const overlays = document.querySelectorAll('.modal-overlay');

  openButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = btn.getAttribute('data-modal-target');
      const modal = document.getElementById(targetId);
      if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
      }
    });
  });

  closeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = btn.closest('.modal-overlay');
      if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  });

  overlays.forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  });
}

// Live Search & Filtering
function initSearchFilter() {
  const quickSearchInput = document.getElementById('globalSearchInput');
  const tableRows = document.querySelectorAll('[data-searchable-row]');

  if (quickSearchInput && tableRows.length > 0) {
    quickSearchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      tableRows.forEach(row => {
        const text = row.innerText.toLowerCase();
        if (text.includes(query)) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
        }
      });
    });
  }

  // Filter dropdown triggers
  const deptFilter = document.getElementById('filterDepartment');
  const typeFilter = document.getElementById('filterFileType');
  const statusFilter = document.getElementById('filterStatus');

  function applyFilters() {
    const deptVal = deptFilter ? deptFilter.value.toLowerCase() : '';
    const typeVal = typeFilter ? typeFilter.value.toLowerCase() : '';
    const statusVal = statusFilter ? statusFilter.value.toLowerCase() : '';

    tableRows.forEach(row => {
      const rowDept = (row.getAttribute('data-department') || '').toLowerCase();
      const rowType = (row.getAttribute('data-type') || '').toLowerCase();
      const rowStatus = (row.getAttribute('data-status') || '').toLowerCase();

      const matchDept = !deptVal || rowDept === deptVal;
      const matchType = !typeVal || rowType === typeVal;
      const matchStatus = !statusVal || rowStatus === statusVal;

      if (matchDept && matchType && matchStatus) {
        row.style.display = '';
      } else {
        row.style.display = 'none';
      }
    });
  }

  if (deptFilter) deptFilter.addEventListener('change', applyFilters);
  if (typeFilter) typeFilter.addEventListener('change', applyFilters);
  if (statusFilter) statusFilter.addEventListener('change', applyFilters);
}

// Folder Cards Active Toggle
function initFolderNavigation() {
  const folderCards = document.querySelectorAll('.folder-card');
  const tableRows = document.querySelectorAll('[data-searchable-row]');

  folderCards.forEach(card => {
    card.addEventListener('click', () => {
      folderCards.forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      const folderName = card.getAttribute('data-folder-name');

      if (folderName && tableRows.length > 0) {
        if (folderName === 'all') {
          tableRows.forEach(r => r.style.display = '');
        } else {
          tableRows.forEach(r => {
            const rowFolder = r.getAttribute('data-folder');
            if (!rowFolder || rowFolder === folderName) {
              r.style.display = '';
            } else {
              r.style.display = 'none';
            }
          });
        }
      }
    });
  });
}

// Table Sorting Simulation
function initTableSorting() {
  const headers = document.querySelectorAll('th[data-sort]');
  headers.forEach(header => {
    header.style.cursor = 'pointer';
    header.addEventListener('click', () => {
      const table = header.closest('table');
      const tbody = table.querySelector('tbody');
      const rows = Array.from(tbody.querySelectorAll('tr'));
      const colIndex = Array.from(header.parentNode.children).indexOf(header);
      const isAsc = header.classList.toggle('asc');

      rows.sort((a, b) => {
        const aText = a.children[colIndex] ? a.children[colIndex].innerText.trim() : '';
        const bText = b.children[colIndex] ? b.children[colIndex].innerText.trim() : '';
        return isAsc ? aText.localeCompare(bText) : bText.localeCompare(aText);
      });

      rows.forEach(r => tbody.appendChild(r));
    });
  });
}

// Upload Form Interaction
function initUploadForm() {
  const dropzone = document.getElementById('uploadDropzone');
  const fileInput = document.getElementById('fileInputHidden');
  const fileNamePreview = document.getElementById('selectedFileNamePreview');
  const uploadForm = document.getElementById('prototypeUploadForm');

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        if (fileNamePreview) {
          fileNamePreview.innerText = `${file.name} (${(file.size / (1024*1024)).toFixed(2)} MB)`;
          fileNamePreview.style.display = 'block';
        }
      }
    });
  }

  if (uploadForm) {
    uploadForm.addEventListener('submit', (e) => {
      e.preventDefault();
      showToast('Document uploaded successfully as a new draft/submission.');
      const modal = uploadForm.closest('.modal-overlay');
      if (modal) modal.classList.remove('active');
      document.body.style.overflow = '';
    });
  }
}

// Approval and Rejection UI actions
function initApprovalActions() {
  const approveButtons = document.querySelectorAll('[data-action-approve]');
  const rejectButtons = document.querySelectorAll('[data-action-reject]');

  approveButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const row = btn.closest('tr');
      if (row) {
        const badge = row.querySelector('.badge');
        if (badge) {
          badge.className = 'badge badge-published';
          badge.innerText = 'Approved';
        }
        btn.parentElement.innerHTML = '<span style="color: var(--success); font-weight: 500; font-size: 12px;">Approved</span>';
        showToast('Document submission approved and published.');
      }
    });
  });

  rejectButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const reasonModal = document.getElementById('rejectionReasonModal');
      if (reasonModal) {
        reasonModal.classList.add('active');
      } else {
        const reason = prompt('Please specify rejection reason for the employee:');
        if (reason) {
          const row = btn.closest('tr');
          if (row) {
            const badge = row.querySelector('.badge');
            if (badge) {
              badge.className = 'badge badge-rejected';
              badge.innerText = 'Rejected';
            }
            btn.parentElement.innerHTML = '<span style="color: var(--danger); font-weight: 500; font-size: 12px;">Rejected</span>';
            showToast(`Submission rejected: "${reason}"`);
          }
        }
      }
    });
  });
}

// Quick Role Switcher
function initRoleSwitcher() {
  const switchBtns = document.querySelectorAll('.role-switch-btn');
  switchBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetRole = btn.getAttribute('data-role');
      if (targetRole) {
        window.location.href = `/dashboard/${targetRole}/`;
      }
    });
  });
}

// Lightweight Toast Notification
function showToast(message) {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `<span>✓</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
