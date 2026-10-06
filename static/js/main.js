// StudyMate - Interactive Frontend Engine

// 1. Web Audio Sound Synthesizer (No external MP3 files needed)
function playSuccessChime() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.type = 'sine';
    osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
    osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.15); // A5
    
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    
    osc.start();
    osc.stop(ctx.currentTime + 0.4);
  } catch (e) {
    console.log("Audio not supported or blocked by user gesture");
  }
}

// 2. Toast Notifications
function showToast(title, message, icon = '🎉') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `
    <div style="font-size: 28px;">${icon}</div>
    <div style="flex: 1;">
      <div style="font-weight: 700; font-size: 14px; color: #0F172A;">${title}</div>
      <div style="font-size: 12px; color: #64748B;">${message}</div>
    </div>
  `;
  
  container.appendChild(toast);
  playSuccessChime();
  
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(20px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// 3. Modal Helpers
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
}

// Close modals when clicking backdrop
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        backdrop.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  });
  
  // Mobile Sidebar Toggle
  const mobileToggle = document.getElementById('mobileToggle');
  const sidebar = document.querySelector('.sidebar');
  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
  }
});

// 4. Interactive Task Toggle via AJAX
async function handleTaskToggle(taskId, checkboxElement) {
  try {
    const response = await fetch(`/tasks/${taskId}/toggle`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    });
    
    const result = await response.json();
    if (result.success) {
      const taskItem = checkboxElement.closest('.task-item');
      if (result.new_status === 1) {
        checkboxElement.classList.add('checked');
        checkboxElement.innerHTML = '✓';
        if (taskItem) taskItem.classList.add('completed');
        showToast('Task Completed!', 'Great job making progress today.', '✨');
      } else {
        checkboxElement.classList.remove('checked');
        checkboxElement.innerHTML = '';
        if (taskItem) taskItem.classList.remove('completed');
      }
      
      // Check for newly unlocked achievements
      if (result.unlocked_achievements && result.unlocked_achievements.length > 0) {
        result.unlocked_achievements.forEach(ach => {
          setTimeout(() => {
            showToast(`Achievement Unlocked! ${ach.icon}`, `${ach.title} (+${ach.points} pts)`, ach.icon);
          }, 600);
        });
      }
    }
  } catch (err) {
    console.error('Failed to toggle task status:', err);
    // Fallback reload if needed
    window.location.reload();
  }
}

// 5. Pomodoro / Study Timer Engine
class StudyTimer {
  constructor() {
    this.totalSeconds = 25 * 60;
    this.remainingSeconds = this.totalSeconds;
    this.timerInterval = null;
    this.isRunning = false;
    this.mode = 'study'; // 'study' or 'break'
    
    this.digitsElem = document.getElementById('timerDigits');
    this.modeElem = document.getElementById('timerModeTag');
    this.startBtn = document.getElementById('startTimerBtn');
    this.pauseBtn = document.getElementById('pauseTimerBtn');
    this.resetBtn = document.getElementById('resetTimerBtn');
    this.subjectSelect = document.getElementById('timerSubjectSelect');
    this.notesInput = document.getElementById('timerNotesInput');
    
    if (this.digitsElem) {
      this.init();
    }
  }
  
  init() {
    this.updateDisplay();
    
    if (this.startBtn) {
      this.startBtn.addEventListener('click', () => this.start());
    }
    if (this.pauseBtn) {
      this.pauseBtn.addEventListener('click', () => this.pause());
    }
    if (this.resetBtn) {
      this.resetBtn.addEventListener('click', () => this.reset());
    }
    
    const studyTab = document.getElementById('tabStudyMode');
    const breakTab = document.getElementById('tabBreakMode');
    
    if (studyTab && breakTab) {
      studyTab.addEventListener('click', () => {
        this.setMode('study', 25);
        studyTab.classList.add('btn-primary');
        studyTab.classList.remove('btn-secondary');
        breakTab.classList.remove('btn-primary');
        breakTab.classList.add('btn-secondary');
      });
      
      breakTab.addEventListener('click', () => {
        this.setMode('break', 5);
        breakTab.classList.add('btn-primary');
        breakTab.classList.remove('btn-secondary');
        studyTab.classList.remove('btn-primary');
        studyTab.classList.add('btn-secondary');
      });
    }
  }
  
  setMode(mode, minutes) {
    this.pause();
    this.mode = mode;
    this.totalSeconds = minutes * 60;
    this.remainingSeconds = this.totalSeconds;
    if (this.modeElem) {
      this.modeElem.innerText = mode === 'study' ? '25 MIN FOCUS SESSION' : '5 MIN RELAX BREAK';
    }
    this.updateDisplay();
  }
  
  start() {
    if (this.isRunning) return;
    this.isRunning = true;
    if (this.startBtn) this.startBtn.style.display = 'none';
    if (this.pauseBtn) this.pauseBtn.style.display = 'inline-flex';
    
    this.timerInterval = setInterval(() => {
      this.remainingSeconds--;
      this.updateDisplay();
      
      if (this.remainingSeconds <= 0) {
        this.completeSession();
      }
    }, 1000);
  }
  
  pause() {
    this.isRunning = false;
    clearInterval(this.timerInterval);
    if (this.startBtn) this.startBtn.style.display = 'inline-flex';
    if (this.pauseBtn) this.pauseBtn.style.display = 'none';
  }
  
  reset() {
    this.pause();
    this.remainingSeconds = this.totalSeconds;
    this.updateDisplay();
  }
  
  updateDisplay() {
    const mins = Math.floor(this.remainingSeconds / 60);
    const secs = this.remainingSeconds % 60;
    const formatted = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    if (this.digitsElem) {
      this.digitsElem.innerText = formatted;
    }
    document.title = `${formatted} - StudyMate`;
  }
  
  async completeSession() {
    this.pause();
    playSuccessChime();
    
    const durationMin = Math.round(this.totalSeconds / 60);
    const subjectId = this.subjectSelect ? this.subjectSelect.value : null;
    const notes = this.notesInput ? this.notesInput.value : '';
    
    if (this.mode === 'study') {
      showToast('Session Finished! 🏆', `Awesome! You studied for ${durationMin} minutes.`, '📚');
      
      try {
        const response = await fetch('/api/timer/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            subject_id: subjectId,
            duration_minutes: durationMin,
            session_type: 'Pomodoro',
            notes: notes
          })
        });
        
        const result = await response.json();
        if (result.success) {
          if (result.unlocked_achievements && result.unlocked_achievements.length > 0) {
            result.unlocked_achievements.forEach(ach => {
              setTimeout(() => {
                showToast(`Badge Unlocked! ${ach.icon}`, `${ach.title} (+${ach.points} pts)`, ach.icon);
              }, 800);
            });
          }
          setTimeout(() => {
            window.location.reload();
          }, 2000);
        }
      } catch (err) {
        console.error('Failed to save study session', err);
      }
    } else {
      showToast('Break Completed!', 'Ready to dive back into learning?', '⚡');
    }
  }
}

// 6. Interactive Monthly Calendar
class StudyCalendar {
  constructor() {
    this.calendarElem = document.getElementById('studyCalendar');
    this.monthTitleElem = document.getElementById('calendarMonthTitle');
    this.prevBtn = document.getElementById('calPrevBtn');
    this.nextBtn = document.getElementById('calNextBtn');
    this.todayBtn = document.getElementById('calTodayBtn');
    
    this.currentDate = new Date();
    this.events = [];
    
    if (this.calendarElem) {
      this.init();
    }
  }
  
  async init() {
    await this.fetchEvents();
    this.render();
    
    if (this.prevBtn) {
      this.prevBtn.addEventListener('click', () => {
        this.currentDate.setMonth(this.currentDate.getMonth() - 1);
        this.render();
      });
    }
    if (this.nextBtn) {
      this.nextBtn.addEventListener('click', () => {
        this.currentDate.setMonth(this.currentDate.getMonth() + 1);
        this.render();
      });
    }
    if (this.todayBtn) {
      this.todayBtn.addEventListener('click', () => {
        this.currentDate = new Date();
        this.render();
      });
    }
  }
  
  async fetchEvents() {
    try {
      const res = await fetch('/api/calendar-events');
      const data = await res.json();
      this.events = data.events || [];
    } catch (e) {
      console.error('Failed to load calendar events', e);
    }
  }
  
  render() {
    const year = this.currentDate.getFullYear();
    const month = this.currentDate.getMonth();
    
    const monthNames = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ];
    
    if (this.monthTitleElem) {
      this.monthTitleElem.innerText = `${monthNames[month]} ${year}`;
    }
    
    const firstDayIndex = new Date(year, month, 1).getDay(); // 0 = Sun
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const daysInPrevMonth = new Date(year, month, 0).getDate();
    
    const today = new Date();
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    
    let html = `
      <div class="cal-header-day">Sun</div>
      <div class="cal-header-day">Mon</div>
      <div class="cal-header-day">Tue</div>
      <div class="cal-header-day">Wed</div>
      <div class="cal-header-day">Thu</div>
      <div class="cal-header-day">Fri</div>
      <div class="cal-header-day">Sat</div>
    `;
    
    // Previous month trailing days
    for (let i = firstDayIndex - 1; i >= 0; i--) {
      const d = daysInPrevMonth - i;
      html += `<div class="cal-day-cell other-month"><div class="day-number">${d}</div></div>`;
    }
    
    // Current month days
    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const isToday = (dateStr === todayStr);
      
      const dayEvents = this.events.filter(e => e.date === dateStr);
      
      let eventsHtml = '';
      dayEvents.slice(0, 3).forEach(ev => {
        eventsHtml += `
          <div class="cal-event-pill" style="background-color: ${ev.color};" title="${ev.title}">
            ${ev.title}
          </div>
        `;
      });
      
      if (dayEvents.length > 3) {
        eventsHtml += `<div style="font-size: 10px; font-weight: 700; color: #4F46E5;">+${dayEvents.length - 3} more</div>`;
      }
      
      html += `
        <div class="cal-day-cell ${isToday ? 'today' : ''}" onclick="showDayDetails('${dateStr}')">
          <div class="day-number">${day}</div>
          <div class="cal-events-wrap">${eventsHtml}</div>
        </div>
      `;
    }
    
    // Next month fill days
    const totalRendered = firstDayIndex + daysInMonth;
    const remaining = (7 - (totalRendered % 7)) % 7;
    for (let i = 1; i <= remaining; i++) {
      html += `<div class="cal-day-cell other-month"><div class="day-number">${i}</div></div>`;
    }
    
    this.calendarElem.innerHTML = html;
  }
}

function showDayDetails(dateStr) {
  const modal = document.getElementById('dayDetailsModal');
  const title = document.getElementById('dayDetailsTitle');
  const body = document.getElementById('dayDetailsBody');
  
  if (!modal || !window._calendarInstance) return;
  
  const dayEvents = window._calendarInstance.events.filter(e => e.date === dateStr);
  
  if (title) title.innerText = `Activities for ${dateStr}`;
  
  if (body) {
    if (dayEvents.length === 0) {
      body.innerHTML = `
        <div style="text-align: center; padding: 24px; color: #64748B;">
          <div style="font-size: 32px; margin-bottom: 8px;">🌱</div>
          <p>No study sessions, exams, or tasks scheduled for this date.</p>
        </div>
      `;
    } else {
      let items = '';
      dayEvents.forEach(ev => {
        items += `
          <div style="padding: 12px; border-radius: 8px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
            <div>
              <div style="font-weight: 700; font-size: 14px; color: #0F172A;">${ev.title}</div>
              <div style="font-size: 12px; color: #64748B;">${ev.time || ''} • <span style="color: ${ev.color}; font-weight: 600;">${ev.category}</span></div>
            </div>
          </div>
        `;
      });
      body.innerHTML = items;
    }
  }
  
  openModal('dayDetailsModal');
}

// Auto-initialize components on page load
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('timerDigits')) {
    window._studyTimer = new StudyTimer();
  }
  if (document.getElementById('studyCalendar')) {
    window._calendarInstance = new StudyCalendar();
  }
});
