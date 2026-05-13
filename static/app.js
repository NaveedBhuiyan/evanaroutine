let schedule = {};
let dragData = null;

// --- Load & Render ---

async function loadSchedule() {
    const res = await fetch('/api/schedule');
    schedule = await res.json();
    render();
}

function render() {
    renderLegend();
    renderTable();
}

function renderLegend() {
    const el = document.getElementById('legend');
    const activities = new Set();
    for (const day of DAYS) {
        for (const [start] of TIME_SLOTS) {
            const a = schedule[day]?.[start];
            if (a) activities.add(a);
        }
    }
    el.innerHTML = '';
    for (const a of activities) {
        const color = COLORS[a] || '#555';
        el.innerHTML += `<span class="legend-item"><span class="legend-dot" style="background:${color}"></span>${a}</span>`;
    }
}

function renderTable() {
    const tbody = document.getElementById('schedule-body');
    tbody.innerHTML = '';

    // Build merge map
    const merged = {};
    for (const day of DAYS) {
        merged[day] = {};
        let i = 0;
        while (i < TIME_SLOTS.length) {
            const start = TIME_SLOTS[i][0];
            const activity = schedule[day]?.[start] || '';
            if (activity) {
                let span = 1;
                while (i + span < TIME_SLOTS.length &&
                       (schedule[day]?.[TIME_SLOTS[i + span][0]] || '') === activity) {
                    span++;
                }
                merged[day][i] = { span, activity, start: TIME_SLOTS[i][0], end: TIME_SLOTS[i + span - 1][1] };
                for (let k = 1; k < span; k++) {
                    merged[day][i + k] = { skip: true };
                }
                i += span;
            } else {
                merged[day][i] = { span: 1, activity: '', start, end: TIME_SLOTS[i][1] };
                i++;
            }
        }
    }

    for (let i = 0; i < TIME_SLOTS.length; i++) {
        const [start, end] = TIME_SLOTS[i];
        const tr = document.createElement('tr');

        // Time cell
        const timeCell = document.createElement('td');
        timeCell.className = 'time-cell';
        timeCell.innerHTML = `${start}<br><span class="time-end">${end}</span>`;
        tr.appendChild(timeCell);

        for (const day of DAYS) {
            const m = merged[day][i];
            if (m.skip) continue;

            const td = document.createElement('td');
            const isCurrentDay = day === CURRENT_DAY;
            td.className = 'slot' + (m.activity ? ' filled' : '') + (isCurrentDay ? ' current-day-col' : '');
            td.dataset.day = day;
            td.dataset.time = start;

            if (m.span > 1) td.rowSpan = m.span;

            if (m.activity) {
                const color = COLORS[m.activity] || '#555';
                td.style.background = color;
                td.style.color = '#fff';
                td.innerHTML = `<span class="activity-name">${m.activity}</span><span class="activity-time">${m.start} – ${m.end}</span>`;
                td.draggable = true;
                td.addEventListener('dragstart', onDragStart);
                td.addEventListener('dragend', onDragEnd);
            }

            td.addEventListener('dragover', onDragOver);
            td.addEventListener('drop', onDrop);
            td.addEventListener('click', () => openModal(day, start));

            tr.appendChild(td);
        }

        tbody.appendChild(tr);
    }
}

// --- Drag & Drop ---

function onDragStart(e) {
    const td = e.currentTarget;
    dragData = { day: td.dataset.day, time: td.dataset.time };
    td.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
}

function onDragEnd(e) {
    e.currentTarget.classList.remove('dragging');
    document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
    dragData = null;
}

function onDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    const td = e.currentTarget;
    if (!td.classList.contains('filled') || (td.dataset.day === dragData?.day && td.dataset.time === dragData?.time)) {
        td.classList.add('drag-over');
    }
}

function onDrop(e) {
    e.preventDefault();
    const td = e.currentTarget;
    td.classList.remove('drag-over');
    if (!dragData) return;

    const dstDay = td.dataset.day;
    const dstTime = td.dataset.time;

    if (dragData.day === dstDay && dragData.time === dstTime) return;

    moveSlot(dragData.day, dragData.time, dstDay, dstTime);
}

async function moveSlot(srcDay, srcTime, dstDay, dstTime) {
    const res = await fetch('/api/schedule/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ srcDay, srcTime, dstDay, dstTime }),
    });
    if (res.ok) {
        schedule[dstDay][dstTime] = schedule[srcDay][srcTime];
        schedule[srcDay][srcTime] = '';
        render();
    }
}

// --- Modal ---

let modalDay = '', modalTime = '';

function openModal(day, time) {
    modalDay = day;
    modalTime = time;
    const activity = schedule[day]?.[time] || '';
    const slot = TIME_SLOTS.find(t => t[0] === time);
    const end = slot ? slot[1] : '';

    document.getElementById('modal-title').textContent = activity ? 'Edit Activity' : 'Add Activity';
    document.getElementById('modal-info').textContent = `${day} · ${time} – ${end}`;
    document.getElementById('modal-input').value = activity;
    document.getElementById('modal-delete').style.display = activity ? 'inline-block' : 'none';
    document.getElementById('modal').style.display = 'flex';

    renderSuggestions(activity);
    document.getElementById('modal-input').focus();
}

function renderSuggestions(current) {
    const el = document.getElementById('modal-suggestions');
    el.innerHTML = '';
    for (const [name, color] of Object.entries(COLORS)) {
        const btn = document.createElement('button');
        btn.className = 'suggestion' + (name === current ? ' active' : '');
        btn.style.borderColor = color;
        btn.style.color = color;
        btn.textContent = name;
        btn.addEventListener('click', () => {
            document.getElementById('modal-input').value = name;
            el.querySelectorAll('.suggestion').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
        el.appendChild(btn);
    }
}

function closeModal() {
    document.getElementById('modal').style.display = 'none';
}

async function saveModal() {
    const activity = document.getElementById('modal-input').value.trim();
    await fetch('/api/schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ day: modalDay, time: modalTime, activity }),
    });
    schedule[modalDay][modalTime] = activity;
    closeModal();
    render();
}

async function deleteModal() {
    await fetch('/api/schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ day: modalDay, time: modalTime, activity: '' }),
    });
    schedule[modalDay][modalTime] = '';
    closeModal();
    render();
}

// --- Init ---

document.getElementById('modal-cancel').addEventListener('click', closeModal);
document.getElementById('modal-save').addEventListener('click', saveModal);
document.getElementById('modal-delete').addEventListener('click', deleteModal);
document.getElementById('modal').addEventListener('click', (e) => {
    if (e.target.id === 'modal') closeModal();
});
document.getElementById('modal-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') saveModal();
    if (e.key === 'Escape') closeModal();
});

loadSchedule();
