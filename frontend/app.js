// CampusPulse Clean Client Controller
// Role-Based Access Control (RBAC), Interactive Action Logging, 
// Single-Vote Endorsements, Confidential Leadership Routing & Historical Archive

let currentView = 'student-report';
let currentSubmissionMode = 'public'; // 'public' | 'anonymous' | 'private'
let currentStudentHistoryTab = 'tickets'; // 'tickets' | 'private'
let currentDrawerIssueId = null;
let currentFeedFilter = 'all';
let allRecipients = [];

// Active Authenticated User & Session State (Loaded dynamically via authentication)
let currentUser = null;
let currentToken = localStorage.getItem('campuspulse_token') || null;

// Modals State
let currentModalIssueId = null;
let currentModalIssueTitle = '';
let currentModalCaseId = '';
let currentReplyMessage = null;

document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

async function initApp() {
  setupEventListeners();
  await initAuth();
  await loadRecipients();
  loadDashboardKPIs();
  loadStudentFeed();
  loadFacultyIssues();
  loadFacultyHotspots();
  triggerNLPPreview();
}

function setupEventListeners() {
  const textarea = document.getElementById('incidentText');
  if (textarea) {
    let debounceTimer;
    textarea.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(triggerNLPPreview, 300);
    });
  }

  // Close demo menu if clicked outside
  document.addEventListener('click', (e) => {
    const demoMenu = document.getElementById('demoMenu');
    const demoBtn = e.target.closest('button');
    if (demoMenu && !demoMenu.classList.contains('hidden')) {
      if (!e.target.closest('#demoMenu') && (!demoBtn || !demoBtn.onclick?.toString().includes('toggleDemoMenu'))) {
        demoMenu.classList.add('hidden');
      }
    }
  });

  // Close modals on escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeAuthModal();
      closeStatusModal();
      closeActionLogModal();
      closeComplaintDrawer();
      closePrivateReplyModal();
    }
  });
}

function toggleDemoMenu() {
  const menu = document.getElementById('demoMenu');
  if (menu) menu.classList.toggle('hidden');
}

// =============================================================================
// RECIPIENTS DIRECTORY & CASCADING ROUTING
// =============================================================================

async function loadRecipients() {
  try {
    const res = await fetch('/api/recipients');
    allRecipients = await res.json();
    handlePrivateRoleChange();
  } catch (err) {
    console.error('Error loading recipients directory:', err);
  }
}

function handlePrivateRoleChange() {
  const roleSelect = document.getElementById('privateRoleSelect');
  const recipSelect = document.getElementById('privateRecipientSelect');
  if (!roleSelect || !recipSelect) return;

  const selectedRole = roleSelect.value.toLowerCase();
  const filtered = allRecipients.filter(r => r.role.toLowerCase() === selectedRole);

  if (filtered.length === 0) {
    recipSelect.innerHTML = `<option value="">No recipient found for role: ${selectedRole.toUpperCase()}</option>`;
    return;
  }

  recipSelect.innerHTML = filtered.map(r => `
    <option value="${r.id}" data-dept="${r.department}" data-name="${r.full_name}" data-role="${r.role}">
      ${r.full_name} — ${r.role.toUpperCase()} (${r.department})
    </option>
  `).join('');

  updateSubmitNotice();
}

// =============================================================================
// AUTHENTICATION & ROLE MANAGEMENT (users.txt)
// =============================================================================

async function initAuth() {
  const savedToken = localStorage.getItem('campuspulse_token');

  if (savedToken) {
    try {
      const res = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${savedToken}` }
      });
      if (res.ok) {
        currentUser = await res.json();
        currentToken = savedToken;
        updateUserNavUI();
        return;
      }
    } catch (e) {
      console.warn('Session check failed:', e);
    }
  }

  // Initial demo seed login via API (saves authenticated token & user)
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: 'student_rohit', password: 'student@123' })
    });
    const data = await res.json();
    if (data.success) {
      currentUser = data.user;
      currentToken = data.token;
      localStorage.setItem('campuspulse_token', currentToken);
    }
  } catch (err) {
    console.error('Initial login setup failed:', err);
  }

  updateUserNavUI();
}

function openAuthModal() {
  const overlay = document.getElementById('authModalOverlay');
  if (overlay) overlay.classList.remove('hidden');
  const errDiv = document.getElementById('loginErrorMessage');
  if (errDiv) errDiv.classList.add('hidden');
}

function closeAuthModal() {
  const overlay = document.getElementById('authModalOverlay');
  if (overlay) overlay.classList.add('hidden');
}

async function quickLoginUser(username, password) {
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();

    if (res.ok && data.success) {
      currentUser = data.user;
      currentToken = data.token;
      localStorage.setItem('campuspulse_user', JSON.stringify(currentUser));
      localStorage.setItem('campuspulse_token', currentToken);

      closeAuthModal();
      showQuickToast(`Switched account: ${currentUser.full_name} (${currentUser.role.toUpperCase()})`, 'success');

      updateUserNavUI();
      loadFacultyIssues();
      loadStudentFeed();
      loadDashboardKPIs();
      if (currentUser.role === 'student') {
        loadStudentHistory();
      } else {
        loadPrivateInbox();
      }
    } else {
      showQuickToast(data.detail || 'Login failed', 'error');
    }
  } catch (err) {
    console.error('Quick login error:', err);
    showQuickToast('Connection error during login.', 'error');
  }
}

async function handleManualLogin(e) {
  e.preventDefault();
  const usernameInput = document.getElementById('loginUsername');
  const passwordInput = document.getElementById('loginPassword');
  const errDiv = document.getElementById('loginErrorMessage');
  const btn = document.getElementById('btnLoginSubmit');

  if (!usernameInput || !passwordInput) return;
  const username = usernameInput.value.trim();
  const password = passwordInput.value.trim();

  if (errDiv) errDiv.classList.add('hidden');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span>Authenticating...</span>`;
  }

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();

    if (res.ok && data.success) {
      currentUser = data.user;
      currentToken = data.token;
      localStorage.setItem('campuspulse_user', JSON.stringify(currentUser));
      localStorage.setItem('campuspulse_token', currentToken);

      closeAuthModal();
      showQuickToast(`Welcome back, ${currentUser.full_name}! (${currentUser.role.toUpperCase()})`, 'success');

      updateUserNavUI();
      loadFacultyIssues();
      loadStudentFeed();
      loadDashboardKPIs();
    } else {
      if (errDiv) {
        errDiv.textContent = data.detail || 'Invalid login ID or password. Check users.txt for dummy credentials.';
        errDiv.classList.remove('hidden');
      }
    }
  } catch (err) {
    if (errDiv) {
      errDiv.textContent = 'Server connection error during login.';
      errDiv.classList.remove('hidden');
    }
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>Log In with Credentials</span><span class="material-symbols-outlined text-sm">login</span>`;
    }
  }
}

// =============================================================================
// ROLE-TAILORED UI & NAVIGATION (NO "RESTRICTED" BADGES FOR STUDENTS)
// =============================================================================

function updateUserNavUI() {
  const avatar = document.getElementById('navUserAvatar');
  const nameEl = document.getElementById('navUserName');
  const badgeEl = document.getElementById('navUserRoleBadge');
  const navTabsContainer = document.getElementById('roleNavTabs');

  if (!currentUser) return;

  const role = currentUser.role.toLowerCase();
  const roleUpper = currentUser.role.toUpperCase();
  if (nameEl) nameEl.textContent = currentUser.full_name;

  // Initials
  const initials = currentUser.full_name.split(' ').map(n => n[0]).slice(0, 2).join('');
  if (avatar) avatar.textContent = initials;

  // Role Badge Styling
  if (badgeEl) {
    badgeEl.textContent = roleUpper;
    if (role === 'student') {
      badgeEl.className = 'px-1.5 py-0.5 rounded text-[10px] font-extrabold uppercase bg-blue-100 text-blue-800 tracking-wide';
      if (avatar) avatar.className = 'w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-extrabold text-xs shadow-xs';
    } else if (role === 'faculty') {
      badgeEl.className = 'px-1.5 py-0.5 rounded text-[10px] font-extrabold uppercase bg-purple-100 text-purple-800 tracking-wide';
      if (avatar) avatar.className = 'w-8 h-8 rounded-full bg-purple-700 text-white flex items-center justify-center font-extrabold text-xs shadow-xs';
    } else if (role === 'hod') {
      badgeEl.className = 'px-1.5 py-0.5 rounded text-[10px] font-extrabold uppercase bg-amber-100 text-amber-800 tracking-wide';
      if (avatar) avatar.className = 'w-8 h-8 rounded-full bg-amber-600 text-white flex items-center justify-center font-extrabold text-xs shadow-xs';
    } else if (role === 'management') {
      badgeEl.className = 'px-1.5 py-0.5 rounded text-[10px] font-extrabold uppercase bg-emerald-100 text-emerald-800 tracking-wide';
      if (avatar) avatar.className = 'w-8 h-8 rounded-full bg-emerald-700 text-white flex items-center justify-center font-extrabold text-xs shadow-xs';
    } else {
      badgeEl.className = 'px-1.5 py-0.5 rounded text-[10px] font-extrabold uppercase bg-cyan-100 text-cyan-800 tracking-wide';
      if (avatar) avatar.className = 'w-8 h-8 rounded-full bg-cyan-700 text-white flex items-center justify-center font-extrabold text-xs shadow-xs';
    }
  }

  // Render Role-Tailored Tabs (NO "Restricted" lock tab anti-pattern!)
  if (navTabsContainer) {
    if (role === 'student') {
      navTabsContainer.innerHTML = `
        <button id="navTab_student-report" onclick="switchView('student-report')" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all">
          Report an Issue
        </button>
        <button id="navTab_student-history" onclick="switchView('student-history')" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition-all flex items-center gap-1.5">
          <span>My Ticket History</span>
        </button>
        <button id="navTab_student-feed" onclick="switchView('student-feed')" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition-all">
          Campus Live Issues
        </button>
      `;
      // If student was on a faculty-only view, redirect to student report view
      if (!['student-report', 'student-history', 'student-feed'].includes(currentView)) {
        switchView('student-report');
      } else {
        updateActiveTabHighlight();
      }
    } else {
      // Faculty, HOD, Management, Staff
      navTabsContainer.innerHTML = `
        <button id="navTab_faculty-console" onclick="switchView('faculty-console')" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all">
          Incident Console
        </button>
        <button id="navTab_faculty-archive" onclick="switchView('faculty-archive')" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition-all">
          Resolved Archive
        </button>
        <button id="navTab_faculty-messages" onclick="switchView('faculty-messages')" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition-all flex items-center gap-1.5">
          <span>Private Messages</span>
          <span id="navPrivateCountBadge" class="hidden px-1.5 py-0.5 rounded-full bg-indigo-100 text-indigo-800 text-[10px] font-bold">0</span>
        </button>
        <button id="navTab_student-report" onclick="switchView('student-report')" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition-all">
          Report Issue
        </button>
      `;
      if (!['faculty-console', 'faculty-archive', 'faculty-messages', 'student-report'].includes(currentView)) {
        switchView('faculty-console');
      } else {
        updateActiveTabHighlight();
      }
    }
  }

  // Drawer status actions visibility
  const drawerNotice = document.getElementById('drawerStudentRestrictedNotice');
  const drawerBtns = document.getElementById('drawerStatusBtnGroup');
  if (drawerNotice && drawerBtns) {
    if (role === 'student') {
      drawerNotice.classList.remove('hidden');
      drawerBtns.classList.add('hidden');
    } else {
      drawerNotice.classList.add('hidden');
      drawerBtns.classList.remove('hidden');
    }
  }

  updateSubmitNotice();
}

function switchView(view) {
  // Legacy view name mapping support
  if (view === 'student') view = 'student-report';
  if (view === 'faculty') view = 'faculty-console';

  // Guard: Students cannot view faculty management consoles
  if (currentUser && currentUser.role === 'student') {
    if (['faculty-console', 'faculty-messages'].includes(view)) {
      showQuickToast('Restricted to faculty & staff accounts.', 'warning');
      view = 'student-report';
    }
  }

  currentView = view;

  // View containers mapping
  const views = {
    'student-report': document.getElementById('viewStudentReport'),
    'student-history': document.getElementById('viewStudentHistory'),
    'student-feed': document.getElementById('viewStudentFeed'),
    'faculty-console': document.getElementById('viewFacultyConsole'),
    'faculty-archive': document.getElementById('viewFacultyArchive'),
    'faculty-messages': document.getElementById('viewFacultyMessages')
  };

  Object.keys(views).forEach(k => {
    if (views[k]) {
      if (k === view) {
        views[k].classList.remove('hidden');
      } else {
        views[k].classList.add('hidden');
      }
    }
  });

  updateActiveTabHighlight();

  // Load target data
  if (view === 'student-report') {
    triggerNLPPreview();
  } else if (view === 'student-history') {
    loadStudentHistory();
  } else if (view === 'student-feed') {
    loadStudentFeed();
  } else if (view === 'faculty-console') {
    loadDashboardKPIs();
    loadFacultyIssues();
    loadFacultyHotspots();
  } else if (view === 'faculty-archive') {
    loadResolvedArchive();
  } else if (view === 'faculty-messages') {
    loadPrivateInbox();
  }
}

function updateActiveTabHighlight() {
  const allTabs = document.querySelectorAll('#roleNavTabs button');
  allTabs.forEach(tab => {
    if (tab.id === `navTab_${currentView}`) {
      tab.classList.add('tab-active');
      tab.classList.remove('text-slate-600');
    } else {
      tab.classList.remove('tab-active');
      tab.classList.add('text-slate-600');
    }
  });
}

// =============================================================================
// SUBMISSION PRIVACY MODES (PUBLIC / ANONYMOUS / PRIVATE CASCADING)
// =============================================================================

function setSubmissionMode(mode) {
  currentSubmissionMode = mode;
  const btnPublic = document.getElementById('modeBtnPublic');
  const btnAnon = document.getElementById('modeBtnAnon');
  const btnPrivate = document.getElementById('modeBtnPrivate');
  const privateContainer = document.getElementById('privateRoutingContainer');
  const submitBtnText = document.getElementById('submitBtnText');
  const submitBtnIcon = document.getElementById('submitBtnIcon');

  // Reset base classes
  [btnPublic, btnAnon, btnPrivate].forEach(b => {
    if (b) b.className = 'p-3.5 rounded-xl border-2 border-slate-200 hover:border-slate-300 bg-white text-slate-700 flex flex-col items-start text-left transition-all';
  });

  if (mode === 'public') {
    if (btnPublic) btnPublic.className = 'p-3.5 rounded-xl border-2 border-brand-600 bg-brand-50/70 text-brand-900 flex flex-col items-start text-left transition-all shadow-xs';
    if (privateContainer) privateContainer.classList.add('hidden');
    if (submitBtnText) submitBtnText.textContent = 'Submit Report';
    if (submitBtnIcon) submitBtnIcon.textContent = 'send';
  } else if (mode === 'anonymous') {
    if (btnAnon) btnAnon.className = 'p-3.5 rounded-xl border-2 border-slate-700 bg-slate-100 text-slate-900 flex flex-col items-start text-left transition-all shadow-xs';
    if (privateContainer) privateContainer.classList.add('hidden');
    if (submitBtnText) submitBtnText.textContent = 'Submit Anonymously';
    if (submitBtnIcon) submitBtnIcon.textContent = 'visibility_off';
  } else if (mode === 'private') {
    if (btnPrivate) btnPrivate.className = 'p-3.5 rounded-xl border-2 border-indigo-600 bg-indigo-50/80 text-indigo-950 flex flex-col items-start text-left transition-all shadow-xs';
    if (privateContainer) privateContainer.classList.remove('hidden');
    if (submitBtnText) submitBtnText.textContent = 'Send Confidential Message';
    if (submitBtnIcon) submitBtnIcon.textContent = 'lock';
    handlePrivateRoleChange();
  }

  updateSubmitNotice();
}

function updateSubmitNotice() {
  const notice = document.getElementById('submitModeNotice');
  if (!notice || !currentUser) return;

  if (currentSubmissionMode === 'public') {
    notice.innerHTML = `Submitting as: <strong>${currentUser.full_name}</strong> (Public Campus Ticket)`;
  } else if (currentSubmissionMode === 'anonymous') {
    notice.innerHTML = `Submitting as: <strong>Anonymous Student</strong> (Identity strictly hidden from everyone)`;
  } else {
    const recipSelect = document.getElementById('privateRecipientSelect');
    const selectedText = recipSelect?.options[recipSelect?.selectedIndex]?.text || 'Leadership';
    notice.innerHTML = `Directing confidential message to: <strong>${selectedText}</strong>`;
  }
}

// --- Real-time Smart Helper ---
async function triggerNLPPreview() {
  const textInput = document.getElementById('incidentText');
  const helper = document.getElementById('smartHelper');
  const categoryEl = document.getElementById('smartHelperCategory');
  const noteEl = document.getElementById('smartHelperNote');
  const locSelect = document.getElementById('locationSelect');

  if (!textInput || !helper) return;
  const text = textInput.value.trim();

  // Auto-detect building from text
  const lower = text.toLowerCase();
  if (lower.includes('wifi') || lower.includes('lab') || lower.includes('turing') || lower.includes('internet')) {
    if (locSelect) locSelect.value = 'cs-lab-3';
  } else if (lower.includes('water') || lower.includes('block c') || lower.includes('shower') || lower.includes('tap') || lower.includes('pani')) {
    if (locSelect) locSelect.value = 'hostel-c-2';
  } else if (lower.includes('dining') || lower.includes('mess') || lower.includes('food') || lower.includes('khana')) {
    if (locSelect) locSelect.value = 'dining-1';
  } else if (lower.includes('light') || lower.includes('staircase') || lower.includes('science') || lower.includes('bijli')) {
    if (locSelect) locSelect.value = 'science-quad';
  } else if (lower.includes('library') || lower.includes('chair') || lower.includes('ac')) {
    if (locSelect) locSelect.value = 'lib-3-east';
  }

  if (text.length < 5) {
    categoryEl.textContent = 'Smart Assistant Active';
    noteEl.textContent = 'Describe the issue to automatically link with existing campus maintenance tickets.';
    return;
  }

  try {
    const res = await fetch('/api/complaints/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    const data = await res.json();

    categoryEl.textContent = `${data.inferred_category} • ${data.urgency === 'CRITICAL' ? 'Urgent Priority' : 'Standard Priority'}`;

    const lightbulbSvg = `<svg class="inline-block w-3.5 h-3.5 mr-1 text-amber-600 align-text-bottom shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="9" y1="18" x2="15" y2="18"/><line x1="10" y1="22" x2="14" y2="22"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/></svg>`;
    const sparkleSvg = `<svg class="inline-block w-3.5 h-3.5 mr-1 text-indigo-600 align-text-bottom shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`;

    if (data.potential_duplicate) {
      noteEl.innerHTML = `${lightbulbSvg}<span>Other students reported a similar problem in this area. Your report will be linked to speed up maintenance!</span>`;
    } else {
      noteEl.innerHTML = `${sparkleSvg}<span>New campus report. Will be sent directly to the response team.</span>`;
    }
  } catch (err) {
    console.error('NLP preview error:', err);
  }
}

function triggerFileUpload() {
  const input = document.getElementById('mediaInput');
  if (input) input.click();
}

function handleFileSelected(event) {
  const file = event.target.files[0];
  const label = document.getElementById('uploadLabel');
  if (file && label) {
    label.textContent = `Attached: ${file.name}`;
    label.classList.add('text-brand-700', 'font-bold');
  }
}

// --- Submit Complaint Form (Public / Anonymous / Private) ---
async function handleFormSubmit(event) {
  event.preventDefault();
  const textInput = document.getElementById('incidentText');
  const locSelect = document.getElementById('locationSelect');
  const btn = document.getElementById('btnSubmitComplaint');

  const text = textInput.value.trim();
  if (!text) {
    showQuickToast('Please enter a description of the issue.', 'warning');
    return;
  }

  btn.disabled = true;
  btn.innerHTML = `<span class="material-symbols-outlined animate-spin text-base">refresh</span><span>Submitting...</span>`;

  try {
    if (currentSubmissionMode === 'private') {
      const recipSelect = document.getElementById('privateRecipientSelect');
      const roleSelect = document.getElementById('privateRoleSelect');
      const subjectInput = document.getElementById('privateSubjectInput');
      const privAnonToggle = document.getElementById('privateAnonToggle');

      const selectedOpt = recipSelect?.options[recipSelect.selectedIndex];
      const recipientId = recipSelect?.value || 'usr-hod-1';
      const recipientName = selectedOpt?.dataset.name || 'Leadership';
      const recipientDept = selectedOpt?.dataset.dept || 'Campus Administration';
      const recipientRole = selectedOpt?.dataset.role || roleSelect?.value || 'hod';
      const isAnon = privAnonToggle ? privAnonToggle.checked : false;
      const subject = subjectInput?.value.trim() || 'Confidential Student Communication';

      const res = await fetch('/api/messages/private', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sender_id: currentUser ? currentUser.id : 'unknown',
          sender_name: currentUser ? currentUser.full_name : 'Verified Student',
          sender_role: currentUser ? currentUser.role : 'student',
          is_anonymous: isAnon,
          recipient_role: recipientRole,
          recipient_id: recipientId,
          recipient_name: recipientName,
          recipient_dept: recipientDept,
          subject: subject,
          message: text,
          category: 'General Grievance',
          urgency: 'STANDARD'
        })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showQuickToast(`Confidential message delivered securely to ${recipientName} (${recipientRole.toUpperCase()}).`, 'success');
        textInput.value = '';
        if (subjectInput) subjectInput.value = '';
        if (currentUser && currentUser.role === 'student') {
          switchView('student-history');
          switchStudentHistoryTab('private');
        }
      } else {
        showQuickToast(data.detail || 'Could not send confidential message.', 'error');
      }
    } else {
      // Public or Anonymous Report
      const isAnon = currentSubmissionMode === 'anonymous';
      const res = await fetch('/api/complaints', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_text: text,
          location_id: locSelect ? locSelect.value : 'hostel-c-2',
          is_anonymous: isAnon,
          student_id: currentUser ? currentUser.id : null,
          student_name: currentUser ? currentUser.full_name : 'Verified Student'
        })
      });

      const result = await res.json();
      if (result.success) {
        if (result.merged_into_existing) {
          showQuickToast(`Thank you! Your report was linked with ${result.case_id} to prioritize repair crews.`, 'success');
        } else {
          showQuickToast(`Thank you! New ticket ${result.case_id} created and dispatched to maintenance.`, 'success');
        }

        textInput.value = '';
        loadStudentFeed();
        loadDashboardKPIs();
        triggerNLPPreview();

        if (currentUser.role === 'student') {
          switchView('student-history');
          switchStudentHistoryTab('tickets');
        }
      } else {
        showQuickToast(result.detail || 'Submission failed.', 'error');
      }
    }
  } catch (err) {
    console.error('Submission error:', err);
    showQuickToast('Could not connect to server.', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span id="submitBtnText">${currentSubmissionMode === 'private' ? 'Send Confidential Message' : currentSubmissionMode === 'anonymous' ? 'Submit Anonymously' : 'Submit Report'}</span><span id="submitBtnIcon" class="material-symbols-outlined text-base">${currentSubmissionMode === 'private' ? 'lock' : currentSubmissionMode === 'anonymous' ? 'visibility_off' : 'send'}</span>`;
  }
}

// =============================================================================
// STUDENT CAMPUS LIVE FEED (ACTIVE ONLY, STRICT 1 VOTE PER TICKET FOR STUDENTS)
// =============================================================================

function filterStudentFeed(type) {
  currentFeedFilter = type;
  const btnAll = document.getElementById('feedFilterAll');
  const btnCrit = document.getElementById('feedFilterCritical');
  if (btnAll) btnAll.className = type === 'all' ? 'px-3.5 py-1.5 rounded-lg bg-white text-slate-900 shadow-xs' : 'px-3.5 py-1.5 rounded-lg text-slate-600 hover:text-slate-900';
  if (btnCrit) btnCrit.className = type === 'critical' ? 'px-3.5 py-1.5 rounded-lg bg-white text-slate-900 shadow-xs' : 'px-3.5 py-1.5 rounded-lg text-slate-600 hover:text-slate-900';
  loadStudentFeed();
}

async function loadStudentFeed() {
  const container = document.getElementById('studentFeedContainer');
  if (!container) return;

  try {
    let url = `/api/issues?active_only=true&limit=30`;
    if (currentUser && currentUser.id) {
      url += `&user_id=${encodeURIComponent(currentUser.id)}`;
    }
    if (currentFeedFilter === 'critical') {
      url += '&priority=critical';
    }

    const res = await fetch(url);
    const issues = await res.json();

    if (!issues || issues.length === 0) {
      container.innerHTML = '<div class="text-center py-12 bg-white rounded-2xl border border-slate-200 text-slate-400 text-xs">No active reports at this time. All campus repairs are up to date!</div>';
      return;
    }

    container.innerHTML = issues.map(iss => renderStudentCard(iss)).join('');
  } catch (err) {
    console.error('Error loading student feed:', err);
    container.innerHTML = '<div class="text-center py-8 text-rose-500 text-xs">Failed to load campus updates.</div>';
  }
}

function renderStudentCard(iss) {
  const isResolved = iss.status === 'RESOLVED' || iss.status === 'CLOSED';
  const isInProgress = iss.status === 'IN_PROGRESS';
  const isAssigned = iss.status === 'ASSIGNED';
  const isStudent = currentUser && currentUser.role === 'student';
  const totalVotes = (iss.complaint_count || 1) + (iss.upvote_count || 0);

  let statusBadge = '';
  if (isResolved) {
    statusBadge = `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Resolved</span>`;
  } else if (isInProgress) {
    statusBadge = `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-900"><span class="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span> In Progress &bull; Maintenance on site</span>`;
  } else if (isAssigned) {
    statusBadge = `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-indigo-100 text-indigo-800">Assigned to ${iss.assigned_team_name}</span>`;
  } else {
    statusBadge = `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-700">Under Review</span>`;
  }

  // Voting CTA or Non-Student Informational Pill
  let endorsementAction = '';
  if (!isResolved) {
    if (isStudent) {
      if (iss.has_voted) {
        endorsementAction = `
          <div class="px-3 py-2 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-800 font-bold text-xs flex items-center gap-1.5 shrink-0 shadow-2xs" title="You endorsed this issue">
            <span class="material-symbols-outlined text-base text-indigo-600">check_circle</span>
            <span>You endorsed this (+${totalVotes})</span>
          </div>
        `;
      } else {
        endorsementAction = `
          <button onclick="upvoteIssue('${iss.id}', event)" class="px-3.5 py-2 rounded-xl bg-brand-50 hover:bg-brand-100 text-brand-900 font-bold text-xs flex items-center gap-2 shrink-0 transition-colors border border-brand-200 active:scale-95 shadow-2xs" title="Click if you also experience this problem (1 vote per ticket)">
            <span class="material-symbols-outlined text-base text-brand-600">thumb_up</span>
            <span>I have this issue too</span>
            <span class="px-2 py-0.5 rounded-full bg-white text-brand-700 font-extrabold text-xs shadow-2xs">+${totalVotes}</span>
          </button>
        `;
      }
    } else {
      // Non-students (Faculty, HOD, Management, Staff) only see informational count!
      endorsementAction = `
        <div class="px-3 py-2 rounded-xl bg-slate-100 border border-slate-200 text-slate-700 font-semibold text-xs flex items-center gap-2 shrink-0" title="Student endorsement count">
          <span class="material-symbols-outlined text-base text-slate-500">groups</span>
          <span><strong>${totalVotes} students</strong> also have this issue</span>
        </div>
      `;
    }
  } else {
    endorsementAction = `<span class="text-xs text-emerald-700 font-semibold self-start sm:self-center">Resolved within SLA</span>`;
  }

  return `
    <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs flex flex-col gap-3 transition-all hover:border-slate-300">
      
      <!-- Top Row: Location & Status -->
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div class="flex items-center gap-2 text-xs font-semibold text-slate-600">
          <span class="material-symbols-outlined text-slate-400 text-base">location_on</span>
          <span>${iss.location_name}</span>
          <span class="text-slate-300">&bull;</span>
          <span class="text-slate-500">${iss.category}</span>
          <span class="text-slate-300">&bull;</span>
          <span class="font-mono text-[11px] text-slate-400">${iss.case_id}</span>
          ${iss.created_at ? `<span class="text-slate-300">&bull;</span><span class="text-slate-400 font-medium">${formatISTTime(iss.created_at)}</span>` : ''}
          ${iss.priority_level === 'CRITICAL' ? '<span class="px-1.5 py-0.5 rounded text-[10px] font-extrabold bg-rose-100 text-rose-700 animate-pulse">Urgent Priority</span>' : ''}
        </div>
        ${statusBadge}
      </div>

      <!-- Main Title & Description -->
      <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
        <div class="flex flex-col gap-1 max-w-2xl">
          <h3 class="text-base font-bold text-slate-900">${iss.title}</h3>
          <p class="text-xs text-slate-600 leading-relaxed">${iss.description || 'Facility engineers are coordinating resolution.'}</p>
        </div>

        ${endorsementAction}
      </div>

      <!-- Footer: Merged student count & Action Log Button -->
      <div class="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between text-xs text-slate-500 gap-2">
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-1.5 font-medium">
            <span class="material-symbols-outlined text-sm text-brand-600">group</span>
            <span><strong>${iss.complaint_count} direct reports</strong> consolidated</span>
          </div>

          <button onclick="openActionLogModal('${iss.id}')" class="inline-flex items-center gap-1 text-[11px] font-bold text-indigo-700 hover:text-indigo-900 bg-indigo-50 hover:bg-indigo-100 px-2.5 py-1 rounded-lg border border-indigo-200/80 transition-colors shadow-2xs">
            <span class="material-symbols-outlined text-[13px]">history</span>
            <span>Show Action Log</span>
          </button>
        </div>

        <!-- 3-Step Simple Progress Indicator -->
        <div class="flex items-center gap-1.5 font-semibold text-[11px]">
          <span class="text-emerald-700 font-bold">&check; Reported</span>
          <span class="text-slate-300">&rarr;</span>
          <span class="${isAssigned || isInProgress || isResolved ? 'text-emerald-700 font-bold' : 'text-slate-400'}">${isAssigned || isInProgress || isResolved ? '&check; Dispatched' : 'Dispatching'}</span>
          <span class="text-slate-300">&rarr;</span>
          <span class="${isResolved ? 'text-emerald-700 font-bold' : 'text-slate-400'}">${isResolved ? '&check; Resolved' : 'Resolution'}</span>
        </div>
      </div>

    </div>
  `;
}

// --- Strict 1-Vote Upvoting Constraint ---
async function upvoteIssue(issueId, event) {
  if (event) event.stopPropagation();

  if (!currentUser || currentUser.role !== 'student') {
    showQuickToast('Permission Denied: Only students can endorse issues with "I have this issue too".', 'warning');
    return;
  }

  try {
    const res = await fetch(`/api/issues/${issueId}/upvote`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: currentUser.id,
        username: currentUser.username,
        user_role: currentUser.role
      })
    });

    const data = await res.json();

    if (res.ok && data.success) {
      const pLevel = data.new_priority_level || data.priority_level || 'ELEVATED';
      showQuickToast(`Added your endorsement! Urgency: ${pLevel} (Score: ${data.new_priority_score}).`, 'success');
      loadStudentFeed();
      loadDashboardKPIs();
      if (currentView === 'faculty-console') loadFacultyIssues();
    } else {
      showQuickToast(data.detail || 'Could not record endorsement.', 'warning');
    }
  } catch (err) {
    console.error('Error upvoting:', err);
    showQuickToast('Connection error.', 'error');
  }
}

// =============================================================================
// STUDENT VIEW: MY TICKET HISTORY & SUBMISSIONS
// =============================================================================

async function loadStudentHistory() {
  const ticketsContainer = document.getElementById('studentTicketsContainer');
  const privateContainer = document.getElementById('studentPrivateContainer');
  const ticketBadge = document.getElementById('badgeMyTicketCount');
  const privateBadge = document.getElementById('badgeMyPrivateCount');

  if (!currentUser) return;

  try {
    // 1. Fetch Reported Tickets
    const resTickets = await fetch(`/api/issues/user/my-tickets?user_id=${encodeURIComponent(currentUser.id)}&student_id=${encodeURIComponent(currentUser.id)}&username=${encodeURIComponent(currentUser.username)}`);
    const tickets = await resTickets.json();

    if (ticketBadge) ticketBadge.textContent = tickets.length;

    if (!tickets || tickets.length === 0) {
      if (ticketsContainer) {
        ticketsContainer.innerHTML = `
          <div class="text-center py-12 bg-white rounded-2xl border border-slate-200 text-slate-500 text-xs">
            <p class="font-bold text-slate-700 text-sm mb-1">No reports logged yet</p>
            <p>Any campus issue you submit will appear here with live resolution tracking.</p>
          </div>
        `;
      }
    } else if (ticketsContainer) {
      ticketsContainer.innerHTML = tickets.map(t => {
        const isResolved = t.issue_status === 'RESOLVED' || t.issue_status === 'CLOSED';
        const dateStr = t.reported_at ? formatISTTime(t.reported_at) : 'Recently';

        return `
          <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs flex flex-col gap-3">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div class="flex items-center gap-2 text-xs font-semibold text-slate-600">
                <span class="font-mono text-brand-700 font-bold">${t.case_id || 'CAMP-NEW'}</span>
                <span class="text-slate-300">&bull;</span>
                <span>${t.location_name || 'Campus'}</span>
                <span class="text-slate-300">&bull;</span>
                <span>${t.category}</span>
                <span class="text-slate-300">&bull;</span>
                <span class="text-slate-400">${dateStr}</span>
              </div>
              <span class="px-2.5 py-1 rounded-full text-xs font-bold ${isResolved ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-900'}">
                ${t.issue_status || 'Under Review'}
              </span>
            </div>

            <div class="flex flex-col gap-1">
              <h3 class="text-sm font-bold text-slate-900">${t.issue_title || t.raw_text}</h3>
              <p class="text-xs text-slate-600 italic bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                "${t.raw_text}"
              </p>
            </div>

            <div class="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
              <div class="flex items-center gap-2 text-slate-500">
                <span class="material-symbols-outlined text-sm text-brand-600">assignment</span>
                <span>Assigned: <strong>${t.assigned_team_name || 'Campus Maintenance'}</strong></span>
                ${t.is_anonymous ? '<span class="text-[11px] text-slate-400">(Submitted Anonymously)</span>' : ''}
              </div>

              ${t.issue_id ? `
                <button onclick="openActionLogModal('${t.issue_id}')" class="inline-flex items-center gap-1 text-[11px] font-bold text-indigo-700 hover:text-indigo-900 bg-indigo-50 hover:bg-indigo-100 px-3 py-1.5 rounded-xl border border-indigo-200 transition-colors shadow-2xs">
                  <span class="material-symbols-outlined text-xs">history</span>
                  <span>Show Action Log</span>
                </button>
              ` : ''}
            </div>
          </div>
        `;
      }).join('');
    }

    // 2. Fetch Sent Private Messages
    const resPriv = await fetch(`/api/messages/sent?user_id=${encodeURIComponent(currentUser.id)}`);
    const privMsgs = await resPriv.json();

    if (privateBadge) privateBadge.textContent = privMsgs.length;

    if (!privMsgs || privMsgs.length === 0) {
      if (privateContainer) {
        privateContainer.innerHTML = `
          <div class="text-center py-12 bg-white rounded-2xl border border-slate-200 text-slate-500 text-xs">
            <p class="font-bold text-slate-700 text-sm mb-1">No confidential messages sent</p>
            <p>You can send private messages directly to HODs or Campus Deans from the reporting form.</p>
          </div>
        `;
      }
    } else if (privateContainer) {
      privateContainer.innerHTML = privMsgs.map(m => {
        const isReplied = m.status === 'REPLIED';
        const dateStr = m.created_at ? formatISTTime(m.created_at) : 'Recently';

        return `
          <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs flex flex-col gap-3">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div class="flex items-center gap-2 text-xs font-semibold text-slate-600">
                <span class="material-symbols-outlined text-indigo-600 text-base">lock</span>
                <span class="font-bold text-indigo-950">To: ${m.recipient_name} (${m.recipient_role.toUpperCase()})</span>
                <span class="text-slate-300">&bull;</span>
                <span class="text-slate-500">${m.recipient_dept}</span>
                <span class="text-slate-300">&bull;</span>
                <span class="text-slate-400">${dateStr}</span>
              </div>
              <span class="px-2.5 py-1 rounded-full text-xs font-bold ${isReplied ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'}">
                ${isReplied ? 'Replied' : 'Pending Response'}
              </span>
            </div>

            <div class="flex flex-col gap-1">
              <h4 class="text-xs font-bold text-slate-800">${m.subject}</h4>
              <p class="text-xs text-slate-700 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                "${m.message}"
              </p>
            </div>

            ${isReplied ? `
              <div class="p-3 rounded-xl bg-emerald-50/70 border border-emerald-200 text-xs text-emerald-950">
                <div class="flex items-center gap-1.5 font-bold mb-1">
                  <span class="material-symbols-outlined text-emerald-700 text-sm">reply</span>
                  <span>Confidential Reply from ${m.replied_by || m.recipient_name}:</span>
                </div>
                <p class="text-xs leading-relaxed italic">
                  "${m.reply_note}"
                </p>
              </div>
            ` : `
              <div class="text-[11px] text-slate-400 italic">
                Awaiting response from ${m.recipient_name}. Only they can view and answer this private message.
              </div>
            `}
          </div>
        `;
      }).join('');
    }

  } catch (err) {
    console.error('Error loading student history:', err);
  }
}

function switchStudentHistoryTab(tab) {
  currentStudentHistoryTab = tab;
  const btnTickets = document.getElementById('tabMyTicketsBtn');
  const btnPrivate = document.getElementById('tabMyPrivateBtn');
  const containerTickets = document.getElementById('studentTicketsContainer');
  const containerPrivate = document.getElementById('studentPrivateContainer');

  if (tab === 'tickets') {
    if (btnTickets) btnTickets.className = 'px-4 py-2 rounded-xl bg-white text-slate-900 shadow-xs transition-all flex items-center gap-2';
    if (btnPrivate) btnPrivate.className = 'px-4 py-2 rounded-xl text-slate-600 hover:text-slate-900 transition-all flex items-center gap-2';
    if (containerTickets) containerTickets.classList.remove('hidden');
    if (containerPrivate) containerPrivate.classList.add('hidden');
  } else {
    if (btnPrivate) btnPrivate.className = 'px-4 py-2 rounded-xl bg-white text-slate-900 shadow-xs transition-all flex items-center gap-2';
    if (btnTickets) btnTickets.className = 'px-4 py-2 rounded-xl text-slate-600 hover:text-slate-900 transition-all flex items-center gap-2';
    if (containerPrivate) containerPrivate.classList.remove('hidden');
    if (containerTickets) containerTickets.classList.add('hidden');
  }
}

// =============================================================================
// FACULTY & STAFF DASHBOARD: INCIDENT CONSOLE (NON-CLIPPING FLEXBOX TABLE)
// =============================================================================

async function loadDashboardKPIs() {
  try {
    const res = await fetch('/api/dashboard/summary');
    const d = await res.json();

    const elActive = document.getElementById('kpiActiveClusters');
    const elTotal = document.getElementById('kpiTotalComplaints');
    const elCritical = document.getElementById('kpiCriticalIssues');
    const elProgress = document.getElementById('kpiInProgress');
    const elResolved = document.getElementById('kpiResolvedIssues');

    if (elActive) elActive.textContent = d.active_clusters;
    if (elTotal) elTotal.textContent = d.total_complaints;
    if (elCritical) elCritical.textContent = d.critical_issues;
    if (elProgress) elProgress.textContent = d.in_progress;
    if (elResolved) elResolved.textContent = d.resolved_issues;
  } catch (err) {
    console.error('Error loading KPI summary:', err);
  }
}

function handleAdminSearch() {
  loadFacultyIssues();
}

async function loadFacultyIssues() {
  const tbody = document.getElementById('adminTableBody');
  if (!tbody) return;

  const cat = document.getElementById('adminCategoryFilter')?.value || 'all';
  const stat = document.getElementById('adminStatusFilter')?.value || 'all';
  const search = document.getElementById('adminSearchInput')?.value.trim() || '';

  let url = '/api/issues?limit=50';
  if (cat !== 'all') url += `&category=${encodeURIComponent(cat)}`;
  if (stat !== 'all') url += `&status=${encodeURIComponent(stat)}`;
  if (search) url += `&search=${encodeURIComponent(search)}`;

  try {
    const res = await fetch(url);
    const issues = await res.json();

    if (!issues || issues.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-center py-10 text-slate-400">No issues found matching filters.</td></tr>';
      return;
    }

    tbody.innerHTML = issues.map(iss => renderFacultyTableRow(iss)).join('');
  } catch (err) {
    console.error('Error loading faculty issues:', err);
    tbody.innerHTML = '<tr><td colspan="8" class="text-center py-10 text-rose-500">Error loading table.</td></tr>';
  }
}

function renderFacultyTableRow(iss) {
  const isResolved = iss.status === 'RESOLVED' || iss.status === 'CLOSED';
  const isCritical = iss.priority_level === 'CRITICAL';

  // Creator details column (strictly hidden if anonymous)
  let creatorHtml = '';
  if (iss.is_anonymous) {
    creatorHtml = `
      <div class="flex items-center gap-1.5 text-slate-500 font-medium">
        <span class="material-symbols-outlined text-sm text-slate-400">visibility_off</span>
        <span class="text-xs">Anonymous Student</span>
      </div>
    `;
  } else {
    creatorHtml = `
      <div class="flex flex-col">
        <span class="font-bold text-slate-900">${iss.creator_name || 'Verified Student'}</span>
        <span class="text-[11px] text-slate-500 font-mono">${iss.creator_id ? 'ID: ' + iss.creator_id : 'Student'}</span>
      </div>
    `;
  }

  return `
    <tr class="hover:bg-slate-50/80 transition-colors">
      <!-- Status Dropdown (Triggers Status Action Modal) -->
      <td class="py-3.5 px-4 whitespace-nowrap">
        <select onchange="promptStatusUpdate('${iss.id}', this.value)" class="px-2.5 py-1.5 rounded-xl text-xs font-bold border ${isResolved ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : iss.status === 'IN_PROGRESS' ? 'bg-amber-50 text-amber-800 border-amber-200' : 'bg-slate-100 text-slate-700 border-slate-200'} cursor-pointer focus:outline-none">
          <option value="OPEN" ${iss.status === 'OPEN' ? 'selected' : ''}>Open</option>
          <option value="ASSIGNED" ${iss.status === 'ASSIGNED' ? 'selected' : ''}>Assigned</option>
          <option value="IN_PROGRESS" ${iss.status === 'IN_PROGRESS' ? 'selected' : ''}>In Progress</option>
          <option value="RESOLVED" ${iss.status === 'RESOLVED' ? 'selected' : ''}>Resolved</option>
          <option value="CLOSED" ${iss.status === 'CLOSED' ? 'selected' : ''}>Closed</option>
        </select>
      </td>

      <!-- Issue & Location -->
      <td class="py-3.5 px-4 min-w-[220px]">
        <div class="flex flex-col">
          <div class="flex items-center gap-1.5">
            <span class="font-bold text-slate-900">${iss.title}</span>
            ${isCritical ? '<span class="px-1.5 py-0.5 rounded text-[10px] font-extrabold bg-rose-100 text-rose-700">Urgent</span>' : ''}
          </div>
          <span class="text-[11px] text-slate-500 font-medium">${iss.location_name}${iss.created_at ? ` &bull; ${formatISTTime(iss.created_at)}` : ''}</span>
        </div>
      </td>

      <!-- Reported By / Creator Column -->
      <td class="py-3.5 px-4 whitespace-nowrap">
        ${creatorHtml}
      </td>

      <!-- Category -->
      <td class="py-3.5 px-4 whitespace-nowrap">
        <span class="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 text-[11px] font-medium">
          ${iss.category}
        </span>
      </td>

      <!-- Merged Student Reports & Endorsements -->
      <td class="py-3.5 px-4 whitespace-nowrap">
        <div class="flex flex-col gap-1 items-start">
          <button onclick="inspectIssueComplaints('${iss.id}')" class="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-brand-50 hover:bg-brand-100 text-brand-800 font-bold transition-colors border border-brand-200 shadow-2xs" title="Click to view all merged student quotes and timestamps">
            <span class="material-symbols-outlined text-xs">group</span>
            <span>${iss.complaint_count} reports</span>
            <span class="material-symbols-outlined text-xs">open_in_new</span>
          </button>
          ${(iss.upvote_count || 0) > 0 ? `
            <span class="inline-flex items-center gap-1 text-[11px] font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-200" title="${iss.upvote_count} students endorsed having this exact issue">
              <span class="material-symbols-outlined text-xs text-indigo-600">thumb_up</span>
              <span>${iss.upvote_count} also endorsed</span>
            </span>
          ` : ''}
        </div>
      </td>

      <!-- Assigned Team -->
      <td class="py-3.5 px-4 whitespace-nowrap text-slate-700 font-medium">
        ${iss.assigned_team_name}
      </td>

      <!-- Ticket -->
      <td class="py-3.5 px-4 whitespace-nowrap font-mono text-slate-600 text-[11px]">
        ${iss.jira_issue_id || '—'}
      </td>

      <!-- Actions: Dynamic Flexbox (Never Cut Off) -->
      <td class="py-3.5 px-4 whitespace-nowrap text-right">
        <div class="flex items-center justify-end gap-2 shrink-0">
          <button onclick="openActionLogModal('${iss.id}')" class="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 text-indigo-700 font-bold transition-colors shadow-2xs shrink-0" title="View all actions and comments on this ticket">
            <span class="material-symbols-outlined text-xs">history</span>
            <span>Show Action Log</span>
          </button>
          <button onclick="inspectIssueComplaints('${iss.id}')" class="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold transition-colors shrink-0">
            Details
          </button>
        </div>
      </td>
    </tr>
  `;
}

// --- Trouble Spots (Hotspots by Location) ---
async function loadFacultyHotspots() {
  const container = document.getElementById('hotspotListContainer');
  if (!container) return;

  try {
    const res = await fetch('/api/dashboard/hotspots');
    const hotspots = await res.json();

    container.innerHTML = hotspots.map(h => {
      const isSevere = h.hotspot_index >= 80;
      const counts = Object.entries(h.category_counts).map(([k, v]) => `${k}: <strong>${v}</strong>`).join(' &bull; ');

      return `
        <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between gap-3 text-xs">
          <div class="flex items-center gap-2.5">
            <div class="w-7 h-7 rounded-lg ${isSevere ? 'bg-rose-100 text-rose-700' : 'bg-slate-200 text-slate-700'} flex items-center justify-center font-bold text-xs shrink-0">
              #${h.rank}
            </div>
            <div>
              <div class="font-bold text-slate-900">${h.location_name}</div>
              <div class="text-[11px] text-slate-500">${counts}</div>
            </div>
          </div>
          <div class="text-right shrink-0">
            <span class="px-2 py-0.5 rounded text-[11px] font-bold ${isSevere ? 'bg-rose-100 text-rose-800' : 'bg-slate-200 text-slate-700'}">
              ${h.active_issue_count} active tickets
            </span>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error('Error loading hotspots:', err);
  }
}

// =============================================================================
// FULL-FLEDGED RESOLVED TICKET ARCHIVE
// =============================================================================

async function loadResolvedArchive() {
  const tbody = document.getElementById('archiveTableBody');
  if (!tbody) return;

  const search = document.getElementById('archiveSearchInput')?.value.trim() || '';
  let url = '/api/issues/archive/resolved?limit=50';
  if (search) url += `&search=${encodeURIComponent(search)}`;

  try {
    const res = await fetch(url);
    const issues = await res.json();

    if (!issues || issues.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center py-12 text-slate-400 text-xs">No resolved records match your query.</td></tr>';
      return;
    }

    tbody.innerHTML = issues.map(iss => {
      const resolvedDate = iss.resolved_at ? formatISTTime(iss.resolved_at) : 'Verified Today';
      const creatorText = iss.is_anonymous ? '<span class="text-slate-400 italic">Anonymous Student</span>' : `<strong>${iss.creator_name || 'Verified Student'}</strong>`;

      return `
        <tr class="hover:bg-slate-50/80 transition-colors">
          <td class="py-3.5 px-4 whitespace-nowrap font-mono text-xs font-bold text-slate-700">
            ${iss.jira_issue_id || iss.case_id}
          </td>
          <td class="py-3.5 px-4 min-w-[240px]">
            <div class="flex flex-col">
              <span class="font-bold text-slate-900">${iss.title}</span>
              <span class="text-[11px] text-slate-500">${iss.location_name}</span>
            </div>
          </td>
          <td class="py-3.5 px-4 whitespace-nowrap text-xs">
            ${creatorText}
          </td>
          <td class="py-3.5 px-4 whitespace-nowrap">
            <span class="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[11px] font-medium">
              ${iss.category}
            </span>
          </td>
          <td class="py-3.5 px-4 whitespace-nowrap text-xs text-slate-600">
            <span class="font-bold text-slate-900">${iss.complaint_count}</span> student reports
          </td>
          <td class="py-3.5 px-4 whitespace-nowrap text-xs text-slate-700 font-medium">
            ${iss.assigned_team_name}
          </td>
          <td class="py-3.5 px-4 whitespace-nowrap text-right">
            <div class="flex items-center justify-end gap-2 shrink-0">
              <button onclick="openActionLogModal('${iss.id}')" class="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 text-indigo-700 font-bold transition-colors shadow-2xs">
                <span class="material-symbols-outlined text-xs">history</span>
                <span>Show Action Log</span>
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error('Error loading resolved archive:', err);
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-10 text-rose-500">Error loading archive.</td></tr>';
  }
}

function handleArchiveSearch() {
  loadResolvedArchive();
}

// =============================================================================
// PRIVATE MESSAGES: RECIPIENT ISOLATED LEADERSHIP INBOX
// =============================================================================

async function loadPrivateInbox() {
  const container = document.getElementById('facultyMessagesContainer');
  const navBadge = document.getElementById('navPrivateCountBadge');
  if (!container || !currentUser) return;

  try {
    const res = await fetch(`/api/messages/inbox?user_id=${encodeURIComponent(currentUser.id)}&role=${encodeURIComponent(currentUser.role)}`);
    const msgs = await res.json();

    if (navBadge) {
      const unreadCount = msgs.filter(m => m.status === 'UNREAD').length;
      if (unreadCount > 0) {
        navBadge.textContent = unreadCount;
        navBadge.classList.remove('hidden');
      } else {
        navBadge.classList.add('hidden');
      }
    }

    if (!msgs || msgs.length === 0) {
      container.innerHTML = `
        <div class="text-center py-16 bg-white rounded-2xl border border-slate-200 text-slate-400 text-xs">
          <span class="material-symbols-outlined text-3xl text-slate-300 mb-2">inbox</span>
          <p class="font-bold text-slate-700 text-sm">Your confidential inbox is clear</p>
          <p class="mt-1">Private messages and grievances addressed to your office will appear securely here.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = msgs.map(m => {
      const isReplied = m.status === 'REPLIED';
      const dateStr = m.created_at ? formatISTTime(m.created_at) : 'Recently';
      const senderText = m.is_anonymous ? 'Anonymous Student' : `${m.sender_name} (${m.sender_role.toUpperCase()})`;

      return `
        <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs flex flex-col gap-3">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div class="flex items-center gap-2 text-xs">
              <span class="material-symbols-outlined text-indigo-600 text-base">lock</span>
              <span class="font-bold text-slate-900">${m.subject}</span>
              <span class="text-slate-300">&bull;</span>
              <span class="text-slate-500">${m.category}</span>
              <span class="text-slate-300">&bull;</span>
              <span class="text-slate-400">${dateStr}</span>
            </div>
            <span class="px-2.5 py-1 rounded-full text-xs font-bold ${isReplied ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-900'}">
              ${isReplied ? 'Replied' : 'Requires Reply'}
            </span>
          </div>

          <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs">
            <div class="flex items-center justify-between text-slate-500 mb-1.5">
              <span>From: <strong class="text-slate-800">${senderText}</strong></span>
              <span>Target: <strong>${m.recipient_name}</strong></span>
            </div>
            <p class="text-xs text-slate-700 leading-relaxed italic bg-white p-2.5 rounded-lg border border-slate-100">
              "${m.message}"
            </p>
          </div>

          ${isReplied ? `
            <div class="p-3 rounded-xl bg-emerald-50/70 border border-emerald-200 text-xs text-emerald-950 flex flex-col gap-1">
              <div class="flex items-center justify-between">
                <span class="font-bold flex items-center gap-1 text-emerald-800">
                  <span class="material-symbols-outlined text-sm">verified</span>
                  Your Sent Response:
                </span>
                <span class="text-[11px] text-emerald-700">${m.replied_at ? formatISTTime(m.replied_at) : ''}</span>
              </div>
              <p class="italic text-slate-700">"${m.reply_note}"</p>
            </div>
          ` : ''}

          <div class="pt-2 border-t border-slate-100 flex items-center justify-end gap-2">
            <button onclick="openPrivateReplyModal('${m.id}', '${escapeHtml(m.subject)}', '${escapeHtml(senderText)}', '${escapeHtml(m.message)}', '${dateStr}')" class="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-xs transition-colors">
              <span class="material-symbols-outlined text-sm">reply</span>
              <span>${isReplied ? 'Send Follow-up Response' : 'Confidential Reply'}</span>
            </button>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Error loading private inbox:', err);
  }
}

function openPrivateReplyModal(id, subject, senderName, messageText, dateStr) {
  currentReplyMessage = { id, subject, senderName, messageText };
  const overlay = document.getElementById('privateReplyModalOverlay');
  const msgIdEl = document.getElementById('modalReplyMsgId');
  const subjectEl = document.getElementById('modalReplySubject');
  const senderEl = document.getElementById('modalReplySenderName');
  const dateEl = document.getElementById('modalReplyDate');
  const msgTextEl = document.getElementById('modalReplyMessageText');
  const actorNameEl = document.getElementById('modalReplyActorName');
  const actorRoleEl = document.getElementById('modalReplyActorRole');
  const commentInput = document.getElementById('privateReplyComment');

  if (msgIdEl) msgIdEl.textContent = id;
  if (subjectEl) subjectEl.textContent = subject;
  if (senderEl) senderEl.textContent = senderName;
  if (dateEl) dateEl.textContent = dateStr;
  if (msgTextEl) msgTextEl.textContent = `"${messageText}"`;
  if (actorNameEl && currentUser) actorNameEl.textContent = currentUser.full_name;
  if (actorRoleEl && currentUser) actorRoleEl.textContent = currentUser.role.toUpperCase();
  if (commentInput) commentInput.value = '';

  if (overlay) overlay.classList.remove('hidden');
}

function closePrivateReplyModal() {
  const overlay = document.getElementById('privateReplyModalOverlay');
  if (overlay) overlay.classList.add('hidden');
  currentReplyMessage = null;
}

async function submitPrivateReply() {
  if (!currentReplyMessage) return;
  const commentInput = document.getElementById('privateReplyComment');
  const btn = document.getElementById('btnSubmitPrivateReply');
  const note = commentInput?.value.trim();

  if (!note) {
    showQuickToast('Please enter a response note before sending.', 'warning');
    return;
  }

  btn.disabled = true;
  btn.innerHTML = `<span>Sending...</span>`;

  try {
    const res = await fetch(`/api/messages/${currentReplyMessage.id}/reply`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reply_note: note,
        replied_by: currentUser ? currentUser.full_name : 'Faculty Member'
      })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      showQuickToast('Confidential response delivered to student.', 'success');
      closePrivateReplyModal();
      loadPrivateInbox();
    } else {
      showQuickToast(data.detail || 'Could not send response.', 'error');
    }
  } catch (err) {
    console.error('Error replying to message:', err);
    showQuickToast('Server connection error.', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>Send Response</span><span class="material-symbols-outlined text-sm">send</span>`;
  }
}

// =============================================================================
// STATUS UPDATE & ACTION LOGGING WITH OPTIONAL COMMENTS
// =============================================================================

async function promptStatusUpdate(issueId, targetStatus) {
  // Enforce student restriction
  if (currentUser && currentUser.role === 'student') {
    showQuickToast('Permission Denied: Students are not permitted to change ticket status.', 'error');
    return;
  }

  currentModalIssueId = issueId;
  const overlay = document.getElementById('statusModalOverlay');
  const selectEl = document.getElementById('modalStatusSelect');
  const commentEl = document.getElementById('modalStatusComment');
  const actorNameEl = document.getElementById('modalStatusActorName');
  const actorRoleEl = document.getElementById('modalStatusActorRole');
  const caseIdEl = document.getElementById('modalStatusCaseId');
  const titleEl = document.getElementById('modalStatusTitle');

  if (selectEl && targetStatus) selectEl.value = targetStatus;
  if (commentEl) commentEl.value = '';
  if (actorNameEl) actorNameEl.textContent = currentUser.full_name;
  if (actorRoleEl) actorRoleEl.textContent = currentUser.role.toUpperCase();

  // Populate ticket title & case ID
  try {
    const res = await fetch(`/api/issues/${issueId}`);
    if (res.ok) {
      const issue = await res.json();
      currentModalCaseId = issue.case_id;
      currentModalIssueTitle = issue.title;
      if (caseIdEl) caseIdEl.textContent = issue.case_id;
      if (titleEl) titleEl.textContent = issue.title;
    }
  } catch (e) {
    console.error(e);
  }

  if (overlay) overlay.classList.remove('hidden');
}

function closeStatusModal() {
  const overlay = document.getElementById('statusModalOverlay');
  if (overlay) overlay.classList.add('hidden');
}

function insertQuickComment(text) {
  const commentEl = document.getElementById('modalStatusComment');
  if (commentEl) {
    commentEl.value = text;
    commentEl.focus();
  }
}

async function submitStatusUpdateModal() {
  if (!currentModalIssueId) return;
  const newStatus = document.getElementById('modalStatusSelect')?.value || 'IN_PROGRESS';
  const commentText = document.getElementById('modalStatusComment')?.value.trim() || null;
  const btn = document.getElementById('btnSubmitStatusModal');

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span>Saving...</span>`;
  }

  try {
    const res = await fetch(`/api/issues/${currentModalIssueId}/status`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...(currentToken ? { 'Authorization': `Bearer ${currentToken}` } : {})
      },
      body: JSON.stringify({
        status: newStatus,
        comment: commentText,
        changed_by: currentUser.full_name,
        changed_by_role: currentUser.role
      })
    });

    const result = await res.json();
    if (res.ok && result.success) {
      closeStatusModal();
      showQuickToast(`Status marked as ${newStatus} by ${currentUser.full_name} (${currentUser.role.toUpperCase()})!`, 'success');
      loadDashboardKPIs();
      loadFacultyIssues();
      loadStudentFeed();
      if (currentDrawerIssueId === currentModalIssueId) {
        inspectIssueComplaints(currentDrawerIssueId);
      }
    } else {
      showQuickToast(result.detail || 'Failed to update status.', 'error');
    }
  } catch (err) {
    console.error('Error submitting status update:', err);
    showQuickToast('Failed to connect to server.', 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>Confirm &amp; Log Action</span><span class="material-symbols-outlined text-sm">check</span>`;
    }
  }
}

// =============================================================================
// SHOW ACTION LOG & COMPLETE AUDIT TRAIL MODAL
// =============================================================================

async function openActionLogModal(issueId) {
  if (!issueId) return;
  const overlay = document.getElementById('actionLogModalOverlay');
  const container = document.getElementById('actionLogTimelineContainer');
  const caseIdEl = document.getElementById('modalActionCaseId');
  const titleEl = document.getElementById('modalActionTitle');

  if (!overlay || !container) return;
  overlay.classList.remove('hidden');
  container.innerHTML = '<div class="text-center py-10 text-slate-400 text-xs">Loading ticket action history...</div>';

  try {
    // Fetch issue details & timeline in parallel
    const [detailRes, timelineRes] = await Promise.all([
      fetch(`/api/issues/${issueId}`),
      fetch(`/api/issues/${issueId}/timeline`)
    ]);

    if (detailRes.ok) {
      const issue = await detailRes.json();
      if (caseIdEl) caseIdEl.textContent = issue.case_id;
      if (titleEl) titleEl.textContent = `${issue.title} • ${issue.location_name}`;
    }

    if (timelineRes.ok) {
      const timeline = await timelineRes.json();
      if (!timeline || timeline.length === 0) {
        container.innerHTML = `
          <div class="text-center py-10 bg-slate-50 rounded-2xl border border-slate-200">
            <span class="material-symbols-outlined text-3xl text-slate-300">hourglass_empty</span>
            <p class="text-xs text-slate-500 font-medium mt-1">No action logs or member status marks recorded for this ticket yet.</p>
          </div>
        `;
        return;
      }

      container.innerHTML = timeline.map(entry => {
        const isResolved = entry.title?.toLowerCase().includes('resolved');
        const isInProgress = entry.title?.toLowerCase().includes('in progress');
        const isDeduplication = entry.title?.toLowerCase().includes('deduplication');
        
        let badgeColor = 'bg-slate-50 text-slate-700 border-slate-200';
        let icon = 'info';
        if (isResolved) {
          badgeColor = 'bg-emerald-50 text-emerald-900 border-emerald-200';
          icon = 'check_circle';
        } else if (isInProgress) {
          badgeColor = 'bg-amber-50 text-amber-900 border-amber-200';
          icon = 'engineering';
        } else if (isDeduplication) {
          badgeColor = 'bg-indigo-50 text-indigo-900 border-indigo-200';
          icon = 'group';
        }

        const roleDisplay = entry.actor_role 
          ? `<span class="px-1.5 py-0.5 rounded text-[9px] font-extrabold uppercase bg-slate-200 text-slate-800 tracking-wide">${entry.actor_role}</span>` 
          : '';
        const actorLine = entry.actor_name 
          ? `Marked by <strong class="text-slate-900">${entry.actor_name}</strong> (Role: ${roleDisplay || 'STAFF'})` 
          : '';

        const formattedTime = entry.timestamp ? formatISTTime(entry.timestamp) : '';

        return `
          <div class="p-3.5 rounded-2xl border ${badgeColor} flex flex-col gap-2 transition-all">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-base text-brand-700">${icon}</span>
                <span class="text-xs font-bold text-slate-900">${entry.title}</span>
              </div>
              <span class="text-[11px] text-slate-500 font-medium">${formattedTime}</span>
            </div>

            ${actorLine ? `
              <div class="text-xs text-slate-700 font-medium flex items-center gap-1.5">
                ${actorLine}
              </div>
            ` : ''}

            ${entry.comment ? `
              <div class="p-2.5 rounded-xl bg-white/90 border border-slate-200 text-xs text-slate-800 font-medium leading-relaxed">
                <strong class="text-slate-500 text-[11px] uppercase block mb-0.5">Comment:</strong>
                &ldquo;${entry.comment}&rdquo;
              </div>
            ` : entry.description && !entry.actor_name ? `
              <div class="text-xs text-slate-600">
                ${entry.description}
              </div>
            ` : ''}
          </div>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Error fetching action log:', err);
    container.innerHTML = '<div class="text-center py-8 text-rose-500 text-xs">Failed to load action log timeline.</div>';
  }
}

function closeActionLogModal() {
  const overlay = document.getElementById('actionLogModalOverlay');
  if (overlay) overlay.classList.add('hidden');
}

// =============================================================================
// MERGED STUDENT TICKETS INSPECTION DRAWER
// =============================================================================

async function inspectIssueComplaints(issueId) {
  currentDrawerIssueId = issueId;
  const drawer = document.getElementById('complaintInspectDrawer');
  const overlay = document.getElementById('drawerOverlay');

  overlay.classList.remove('hidden');
  drawer.classList.remove('translate-x-full');

  updateUserNavUI();

  try {
    const res = await fetch(`/api/issues/${issueId}`);
    const detail = await res.json();

    document.getElementById('drawerCaseId').textContent = detail.case_id;
    document.getElementById('drawerTitle').textContent = detail.title;
    document.getElementById('drawerSubtitle').textContent = `${detail.location_name} • ${detail.complaint_count} Student Reports Merged`;
    document.getElementById('drawerComplaintCount').textContent = detail.complaint_count;
    document.getElementById('drawerTeamName').textContent = detail.assigned_team_name;
    document.getElementById('drawerJiraKey').textContent = detail.jira_issue_id || 'Not Assigned';

    const statusBadge = document.getElementById('drawerStatusBadge');
    statusBadge.textContent = detail.status;
    statusBadge.className = detail.status === 'RESOLVED' 
      ? 'px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800'
      : detail.status === 'IN_PROGRESS'
      ? 'px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800'
      : 'px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700';

    const list = document.getElementById('drawerComplaintsList');
    if (!detail.complaints || detail.complaints.length === 0) {
      list.innerHTML = '<div class="text-center py-6 text-slate-400 text-xs">No individual student complaints logged yet.</div>';
      return;
    }

    list.innerHTML = detail.complaints.map(c => `
      <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
        <div class="flex items-center justify-between text-slate-500 mb-1 text-[11px]">
          <span class="font-bold text-slate-700">${c.id}</span>
          <span>${c.created_at ? formatISTTime(c.created_at) : 'Recently'}</span>
        </div>
        <p class="text-slate-800 font-medium my-1 leading-relaxed">"${c.raw_text}"</p>
        <div class="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-200/60 mt-2">
          <span>${c.is_anonymous ? 'Submitted anonymously' : 'Verified Student'}</span>
          <span class="text-emerald-700 font-semibold">&bull; Merged into master ticket</span>
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Error inspecting issue complaints:', err);
  }
}

function closeComplaintDrawer() {
  const drawer = document.getElementById('complaintInspectDrawer');
  const overlay = document.getElementById('drawerOverlay');
  drawer.classList.add('translate-x-full');
  overlay.classList.add('hidden');
}

// =============================================================================
// PRESENTATION DEMO TRIGGERS & UTILITIES
// =============================================================================

async function runDeckDemoScenario() {
  showQuickToast('Simulating 4 students reporting water outage in Block C...', 'warning');

  try {
    const res = await fetch('/api/demo/run-scenario', { method: 'POST' });
    const data = await res.json();

    let delay = 600;
    data.results.forEach((r, i) => {
      setTimeout(() => {
        showQuickToast(`Student ${i + 1} (${r.student}): "${r.complaint_text}" → Merged into ${r.result.case_id}`, 'success');
        loadStudentFeed();
        loadDashboardKPIs();
        if (currentView === 'faculty-console') loadFacultyIssues();
      }, delay);
      delay += 800;
    });
  } catch (err) {
    console.error('Demo error:', err);
  }
}

async function testJiraWebhook() {
  try {
    const res = await fetch('/api/webhooks/jira', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        issue: {
          key: 'CAMP-421',
          fields: { status: { name: 'Resolved' } }
        }
      })
    });
    const result = await res.json();
    showQuickToast(`Ticket CAMP-421 marked as RESOLVED by maintenance crew!`, 'success');
    loadDashboardKPIs();
    loadFacultyIssues();
    loadStudentFeed();
    loadResolvedArchive();
  } catch (err) {
    console.error('Jira webhook test error:', err);
  }
}

async function seedDatabase(notify = false) {
  try {
    await fetch('/api/demo/seed', { method: 'POST' });
    if (notify) showQuickToast('Database reset to clean demo state.', 'success');
    loadStudentFeed();
    loadDashboardKPIs();
    loadFacultyIssues();
    loadFacultyHotspots();
    loadResolvedArchive();
  } catch (err) {
    console.error('Seed error:', err);
  }
}

function showQuickToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  const bgColor = type === 'success' ? 'bg-slate-900 text-white' :
                  type === 'warning' ? 'bg-amber-600 text-white' :
                  type === 'error' ? 'bg-rose-600 text-white' :
                  'bg-slate-800 text-white';

  toast.className = `pointer-events-auto px-4 py-3 rounded-xl shadow-xl text-xs font-semibold flex items-center gap-2 fade-in ${bgColor}`;
  toast.innerHTML = `
    <span class="material-symbols-outlined text-base">
      ${type === 'success' ? 'check_circle' : type === 'warning' ? 'priority_high' : 'info'}
    </span>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.25s ease';
    setTimeout(() => toast.remove(), 250);
  }, 4500);
}

function escapeHtml(str) {
  return (str || '')
    .replace(/'/g, "\\'")
    .replace(/"/g, '&quot;');
}

function formatISTTime(dateStr, includeSeconds = false) {
  if (!dateStr) return 'Recently';
  try {
    let normalizedStr = String(dateStr).trim();
    if (!normalizedStr.endsWith('Z') && !/[+-]\d{2}:?\d{2}$/.test(normalizedStr)) {
      normalizedStr += 'Z';
    }
    const d = new Date(normalizedStr);
    if (isNaN(d.getTime())) return dateStr;
    const options = {
      timeZone: 'Asia/Kolkata',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    };
    if (includeSeconds) {
      options.second = '2-digit';
    }
    return `${d.toLocaleString('en-IN', options)} IST`;
  } catch (e) {
    return dateStr;
  }
}

