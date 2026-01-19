
const DASHBOARD_STORAGE_KEY = 'ruoom.dashboard.v1';

function dashboardGetLocationIdFromUrl() {
  const url = new URL(window.location.href);
  return url.searchParams.get('location_id');
}

function dashboardFormatMoney(value, currency) {
  const amount = Number(value || 0);
  const curr = currency || 'USD';
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: curr,
      maximumFractionDigits: 0,
    }).format(amount);
  } catch (e) {
    return `${amount.toFixed(0)} ${curr}`;
  }
}

function dashboardGenerateDemoRevenue(days) {
  const count = Math.max(7, Math.min(90, parseInt(days || 30, 10) || 30));
  const labels = [];
  const series = [];
  const now = new Date();
  let level = 1200 + Math.round(Math.random() * 600);
  for (let i = count - 1; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(now.getDate() - i);
    labels.push(`${d.getMonth() + 1}/${d.getDate()}`);

    const drift = (Math.random() - 0.45) * 90;
    const shock = (Math.random() < 0.08) ? (700 + Math.random() * 1400) : 0;
    const dip = (Math.random() < 0.06) ? -(250 + Math.random() * 550) : 0;
    level = Math.max(150, level + drift + shock + dip);

    const jitter = (Math.random() - 0.5) * 120;
    series.push(Math.max(0, Math.round(level + jitter)));
  }
  const total = series.reduce((a, b) => a + b, 0);
  return {
    labels,
    series,
    total,
    currency: 'USD',
    is_demo: true,
  };
}

function dashboardGenerateDemoNewCustomers(days) {
  const count = Math.max(7, Math.min(90, parseInt(days || 30, 10) || 30));
  const labels = [];
  const series = [];
  const now = new Date();
  let baseline = 6 + Math.random() * 6;
  for (let i = count - 1; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(now.getDate() - i);
    labels.push(`${d.getMonth() + 1}/${d.getDate()}`);

    baseline = Math.max(2, baseline + (Math.random() - 0.5) * 1.2);
    const volatility = (Math.random() - 0.5) * 6;
    const promoSpike = (Math.random() < 0.07) ? (8 + Math.random() * 14) : 0;
    const value = Math.max(0, Math.round(baseline + volatility + promoSpike));
    series.push(value);
  }
  return {
    labels,
    series,
    is_demo: true,
  };
}

function dashboardGenerateDemoActionCenter() {
  return {
    approvals: [
      {
        request: 'Booking #10431 (Room A) — 3 hrs',
        customer: 'Acme Events',
        due: 'Today',
        status: 'Pending',
        href: '/administration/booking/',
        cta: 'Review',
      },
      {
        request: 'Booking #10438 (Room C) — 1 day',
        customer: 'Northwind',
        due: 'Tomorrow',
        status: 'Pending',
        href: '/administration/booking/',
        cta: 'Review',
      },
    ],
    issues: [
      {
        issue: 'Projector not powering on (Room B)',
        reported_by: 'Staff',
        opened: '2 days ago',
        severity: 'High',
        href: '/administration/rooms/',
        cta: 'View',
      },
      {
        issue: 'AC running warm (Room D)',
        reported_by: 'Customer',
        opened: 'Yesterday',
        severity: 'Medium',
        href: '/administration/rooms/',
        cta: 'View',
      },
    ],
    reminders: [
      {
        reminder: 'Invoice #8832 due',
        recipient: 'Globex',
        scheduled: 'Tomorrow 9:00 AM',
        channel: 'Email',
        href: '/administration/invoice/',
        cta: 'Open',
      },
      {
        reminder: 'Deposit follow-up',
        recipient: 'Initech',
        scheduled: 'Fri 2:00 PM',
        channel: 'SMS',
        href: '/administration/invoice/',
        cta: 'Open',
      },
      {
        reminder: 'Contract signature nudge',
        recipient: 'Umbrella Co.',
        scheduled: 'Mon 10:00 AM',
        channel: 'Email',
        href: '/administration/invoice/',
        cta: 'Open',
      },
    ],
  };
}

function dashboardFormatUpdatedAgo(dateObj) {
  const diffMs = Date.now() - dateObj.getTime();
  const diffMin = Math.max(0, Math.floor(diffMs / 60000));
  if (diffMin < 1) return 'Updated just now';
  if (diffMin < 60) return `Updated ${diffMin} min ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `Updated ${diffHr} hr ago`;
  const diffDay = Math.floor(diffHr / 24);
  return `Updated ${diffDay} day${diffDay === 1 ? '' : 's'} ago`;
}

function dashboardGetDefaultConfig() {
  return {
    days: 30,
    widgetOrder: [
      'kpi_customers',
      'kpi_staff',
      'kpi_locations',
      'kpi_rooms',
      'revenue_tracking',
      'action_center',
      'chart_new_customers',
      'activity_feed',
    ],
    hiddenWidgets: [],
  };
}

function dashboardLoadConfig() {
  try {
    const raw = localStorage.getItem(DASHBOARD_STORAGE_KEY);
    if (!raw) return dashboardGetDefaultConfig();
    const parsed = JSON.parse(raw);
    return {
      ...dashboardGetDefaultConfig(),
      ...parsed,
      widgetOrder: Array.isArray(parsed.widgetOrder) ? parsed.widgetOrder : dashboardGetDefaultConfig().widgetOrder,
      hiddenWidgets: Array.isArray(parsed.hiddenWidgets) ? parsed.hiddenWidgets : [],
    };
  } catch (e) {
    return dashboardGetDefaultConfig();
  }
}

function dashboardSaveConfig(cfg) {
  localStorage.setItem(DASHBOARD_STORAGE_KEY, JSON.stringify(cfg));
}

function dashboardSetText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function dashboardApplyWidgetVisibility(cfg) {
  const hidden = new Set(cfg.hiddenWidgets || []);
  $('#dashboard-widgets [data-widget]').each(function () {
    const key = $(this).attr('data-widget');
    if (hidden.has(key)) {
      $(this).addClass('dashboard-widget-hidden');
    } else {
      $(this).removeClass('dashboard-widget-hidden');
    }
  });
}

function dashboardApplyWidgetOrder(cfg) {
  const container = document.getElementById('dashboard-widgets');
  if (!container) return;

  const current = Array.from(container.querySelectorAll('[data-widget]'));
  const byKey = {};
  current.forEach((el) => {
    byKey[el.getAttribute('data-widget')] = el;
  });

  const order = cfg.widgetOrder || [];
  order.forEach((key) => {
    if (byKey[key]) container.appendChild(byKey[key]);
  });

  current.forEach((el) => {
    if (!order.includes(el.getAttribute('data-widget'))) {
      container.appendChild(el);
    }
  });
}

function dashboardBuildWidgetOrderFromDom() {
  const container = document.getElementById('dashboard-widgets');
  if (!container) return [];
  return Array.from(container.querySelectorAll('[data-widget]')).map((el) => el.getAttribute('data-widget'));
}

function dashboardSetWidgetHidden(cfg, key, hidden) {
  const nextHidden = new Set(cfg.hiddenWidgets || []);
  if (hidden) nextHidden.add(key);
  else nextHidden.delete(key);
  cfg.hiddenWidgets = Array.from(nextHidden);
  dashboardSaveConfig(cfg);
  dashboardApplyWidgetVisibility(cfg);
  dashboardUpdateWidgetControlState(cfg);
}

function dashboardEnsureWidgetControls(cfg) {
  const container = document.getElementById('dashboard-widgets');
  if (!container) return;

  container.querySelectorAll('[data-widget]').forEach((widgetEl) => {
    if (widgetEl.querySelector('.dashboard-widget-controls')) return;

    const key = widgetEl.getAttribute('data-widget');
    const controls = document.createElement('div');
    controls.className = 'dashboard-widget-controls';

    const handle = document.createElement('button');
    handle.type = 'button';
    handle.className = 'dashboard-widget-control dashboard-widget-handle';
    handle.title = 'Drag to move';
    handle.setAttribute('draggable', 'true');
    handle.innerHTML = '<i class="fe fe-move"></i>';

    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'dashboard-widget-control dashboard-widget-visibility';
    toggle.title = 'Hide/Show';
    toggle.innerHTML = '<i class="fe fe-eye"></i>';
    toggle.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const isHidden = (cfg.hiddenWidgets || []).includes(key);
      dashboardSetWidgetHidden(cfg, key, !isHidden);
    });

    controls.appendChild(handle);
    controls.appendChild(toggle);
    widgetEl.appendChild(controls);
  });

  dashboardUpdateWidgetControlState(cfg);
}

function dashboardUpdateWidgetControlState(cfg) {
  const container = document.getElementById('dashboard-widgets');
  if (!container) return;
  const hidden = new Set(cfg.hiddenWidgets || []);
  container.querySelectorAll('[data-widget]').forEach((widgetEl) => {
    const key = widgetEl.getAttribute('data-widget');
    const btn = widgetEl.querySelector('.dashboard-widget-visibility');
    if (!btn) return;
    btn.innerHTML = hidden.has(key)
      ? '<i class="fe fe-eye-off"></i>'
      : '<i class="fe fe-eye"></i>';
  });
}

function dashboardEnableInlineEditMode(cfg) {
  const container = document.getElementById('dashboard-widgets');
  if (!container) return;

  container.classList.add('dashboard-editing');
  dashboardEnsureWidgetControls(cfg);

  let dragSrcEl = null;
  let dragSrcKey = null;

  const clearDropTargets = () => {
    container.querySelectorAll('.dashboard-drop-target').forEach((el) => el.classList.remove('dashboard-drop-target'));
  };

  const onHandleDragStart = (e) => {
    const widgetEl = e.target.closest('[data-widget]');
    if (!widgetEl) return;
    dragSrcEl = widgetEl;
    dragSrcKey = widgetEl.getAttribute('data-widget');
    widgetEl.classList.add('dashboard-dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', dragSrcKey);
  };

  const onHandleDragEnd = () => {
    if (dragSrcEl) dragSrcEl.classList.remove('dashboard-dragging');
    dragSrcEl = null;
    dragSrcKey = null;
    clearDropTargets();
  };

  const onWidgetDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    const targetEl = e.currentTarget;
    if (targetEl) targetEl.classList.add('dashboard-drop-target');
  };

  const onWidgetDragLeave = (e) => {
    const targetEl = e.currentTarget;
    if (targetEl) targetEl.classList.remove('dashboard-drop-target');
  };

  const onWidgetDrop = (e) => {
    e.preventDefault();
    const targetEl = e.currentTarget;
    if (!dragSrcEl || !targetEl || dragSrcEl === targetEl) return;

    const rect = targetEl.getBoundingClientRect();
    const before = e.clientY < rect.top + rect.height / 2;

    container.insertBefore(dragSrcEl, before ? targetEl : targetEl.nextSibling);
    clearDropTargets();

    cfg.widgetOrder = dashboardBuildWidgetOrderFromDom();
    dashboardSaveConfig(cfg);
  };

  container.querySelectorAll('.dashboard-widget-handle').forEach((h) => {
    h.addEventListener('dragstart', onHandleDragStart);
    h.addEventListener('dragend', onHandleDragEnd);
  });

  container.querySelectorAll('[data-widget]').forEach((el) => {
    el.addEventListener('dragover', onWidgetDragOver);
    el.addEventListener('dragleave', onWidgetDragLeave);
    el.addEventListener('drop', onWidgetDrop);
  });

  container._dashboardInlineEdit = {
    onHandleDragStart,
    onHandleDragEnd,
    onWidgetDragOver,
    onWidgetDragLeave,
    onWidgetDrop,
  };
}

function dashboardDisableInlineEditMode() {
  const container = document.getElementById('dashboard-widgets');
  if (!container) return;
  container.classList.remove('dashboard-editing');
  container.querySelectorAll('.dashboard-drop-target').forEach((el) => el.classList.remove('dashboard-drop-target'));
  container.querySelectorAll('.dashboard-dragging').forEach((el) => el.classList.remove('dashboard-dragging'));
}

function dashboardRenderCustomizeList(cfg) {
  const list = document.getElementById('dashboard-customize-list');
  if (!list) return;
  list.innerHTML = '';

  const hidden = new Set(cfg.hiddenWidgets || []);
  const widgets = cfg.widgetOrder || [];

  const titles = {
    kpi_customers: 'Customers',
    kpi_staff: 'Staff',
    kpi_locations: 'Locations',
    kpi_rooms: 'Rooms',
    revenue_tracking: 'Revenue',
    action_center: 'Action Center',
    chart_new_customers: 'New customers',
    activity_feed: 'Activity',
  };

  widgets.forEach((key) => {
    const row = document.createElement('div');
    row.className = 'list-group-item d-flex align-items-center justify-content-between';
    row.setAttribute('data-widget-key', key);
    row.draggable = true;

    const left = document.createElement('div');
    left.className = 'd-flex align-items-center';

    const handle = document.createElement('span');
    handle.className = 'dashboard-card-handle mr-2 text-muted';
    handle.innerHTML = '<i class="fe fe-move"></i>';

    const label = document.createElement('div');
    label.className = 'font-weight-bold';
    label.textContent = titles[key] || key;

    left.appendChild(handle);
    left.appendChild(label);

    const right = document.createElement('div');
    right.className = 'custom-control custom-switch';

    const input = document.createElement('input');
    input.type = 'checkbox';
    input.className = 'custom-control-input';
    input.id = `dash-toggle-${key}`;
    input.checked = !hidden.has(key);
    input.addEventListener('change', () => {
      const nextHidden = new Set(cfg.hiddenWidgets || []);
      if (input.checked) {
        nextHidden.delete(key);
      } else {
        nextHidden.add(key);
      }
      cfg.hiddenWidgets = Array.from(nextHidden);
      dashboardSaveConfig(cfg);
      dashboardApplyWidgetVisibility(cfg);
    });

    const switchLabel = document.createElement('label');
    switchLabel.className = 'custom-control-label';
    switchLabel.setAttribute('for', input.id);

    right.appendChild(input);
    right.appendChild(switchLabel);

    row.appendChild(left);
    row.appendChild(right);
    list.appendChild(row);
  });

  let dragSrc = null;
  list.querySelectorAll('[draggable="true"]').forEach((item) => {
    item.addEventListener('dragstart', (e) => {
      dragSrc = item;
      e.dataTransfer.effectAllowed = 'move';
    });
    item.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
    });
    item.addEventListener('drop', (e) => {
      e.preventDefault();
      if (!dragSrc || dragSrc === item) return;

      const srcKey = dragSrc.getAttribute('data-widget-key');
      const dstKey = item.getAttribute('data-widget-key');
      const order = cfg.widgetOrder.slice();

      const srcIdx = order.indexOf(srcKey);
      const dstIdx = order.indexOf(dstKey);
      if (srcIdx === -1 || dstIdx === -1) return;

      order.splice(srcIdx, 1);
      order.splice(dstIdx, 0, srcKey);

      cfg.widgetOrder = order;
      dashboardSaveConfig(cfg);
      dashboardApplyWidgetOrder(cfg);
      dashboardRenderCustomizeList(cfg);
    });
  });
}

let chartNewCustomers = null;
let chartRevenueSparkline = null;

function dashboardRenderChartNewCustomers(data) {
  const canvas = document.getElementById('chart-new-customers');
  if (!canvas) return;

  const input = (data && Array.isArray(data.series) && data.series.length) ? data : dashboardGenerateDemoNewCustomers(30);
  const labels = input.labels || [];
  const series = input.series || [];

  const sum = series.reduce((a, b) => a + b, 0);
  dashboardSetText('chart-new-customers-total', `${sum}`);

  if (chartNewCustomers) {
    chartNewCustomers.destroy();
    chartNewCustomers = null;
  }

  chartNewCustomers = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'New customers',
          data: series,
          borderColor: '#2C7BE5',
          backgroundColor: 'rgba(44, 123, 229, 0.12)',
          fill: true,
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.35,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { mode: 'index', intersect: false },
      },
      scales: {
        x: { display: true, ticks: { maxTicksLimit: 8 } },
        y: { display: true, beginAtZero: true, ticks: { maxTicksLimit: 5 } },
      },
    },
  });
}

function dashboardRenderRevenue(revenue, days) {
  const canvas = document.getElementById('chart-revenue-sparkline');
  if (!canvas) return;

  const data = revenue && Array.isArray(revenue.series) && revenue.series.length
    ? revenue
    : dashboardGenerateDemoRevenue(days);

  const total = (typeof data.total === 'number')
    ? data.total
    : (Array.isArray(data.series) ? data.series.reduce((a, b) => a + b, 0) : 0);

  dashboardSetText('revenue-total', dashboardFormatMoney(total, data.currency));
  dashboardSetText('revenue-sub', `Revenue in last ${days} days${data.is_demo ? ' (demo)' : ''}`);

  if (chartRevenueSparkline) {
    chartRevenueSparkline.destroy();
    chartRevenueSparkline = null;
  }

  chartRevenueSparkline = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: {
      labels: data.labels || [],
      datasets: [
        {
          label: 'Revenue',
          data: data.series || [],
          borderColor: '#2C7BE5',
          backgroundColor: 'rgba(44, 123, 229, 0.12)',
          fill: true,
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.35,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: (ctx) => dashboardFormatMoney(ctx.parsed.y, data.currency),
          },
        },
      },
      scales: {
        x: { display: false },
        y: { display: false },
      },
    },
  });
}

function dashboardRenderActionCenter(items) {
  const container = document.getElementById('dashboard-action-center');
  if (!container) return;

  const demo = dashboardGenerateDemoActionCenter();
  const grouped = (items && typeof items === 'object' && !Array.isArray(items))
    ? items
    : demo;

  const approvals = Array.isArray(grouped.approvals) ? grouped.approvals : demo.approvals;
  const issues = Array.isArray(grouped.issues) ? grouped.issues : demo.issues;
  const reminders = Array.isArray(grouped.reminders) ? grouped.reminders : demo.reminders;

  const chip = (text, tone) => {
    const safe = (text || '').toString();
    const t = tone || 'gray';
    return `<span class="dashboard-chip dashboard-chip-${t}">${safe}</span>`;
  };

  const tableWrap = (key, title, icon, rowsHtml) => {
    return `
      <div class="dashboard-action-section ${key} mb-3">
        <div class="d-flex align-items-center justify-content-between mb-2">
          <div class="dashboard-action-section-title font-weight-bold">
            <i class="fe ${icon}"></i>
            <span>${title}</span>
          </div>
        </div>
        <div class="table-responsive">
          <table class="table table-sm mb-0 dashboard-action-table">
            <tbody>
              ${rowsHtml}
            </tbody>
          </table>
        </div>
      </div>
    `;
  };

  const actionBtn = (href, text) => href ? `<a class="btn btn-sm btn-white" href="${href}">${text || 'Open'}</a>` : '';

  const approvalsRows = approvals.map((r) => {
    const statusTone = (r.status || '').toLowerCase().includes('pending') ? 'amber' : 'gray';
    return `
      <tr>
        <td>
          <div class="font-weight-bold">${r.request || ''}</div>
          <div class="text-muted small">${r.customer || ''}</div>
        </td>
        <td class="text-muted small" style="white-space:nowrap;">${r.due || ''}</td>
        <td style="white-space:nowrap;">${chip(r.status || '', statusTone)}</td>
        <td class="text-right">${actionBtn(r.href, r.cta || 'Review')}</td>
      </tr>
    `;
  }).join('');

  const issuesRows = issues.map((r) => {
    const sev = (r.severity || '').toLowerCase();
    const sevTone = sev.includes('high') ? 'red' : (sev.includes('medium') ? 'amber' : 'gray');
    return `
      <tr>
        <td>
          <div class="font-weight-bold">${r.issue || ''}</div>
          <div class="text-muted small">Reported by ${r.reported_by || ''}</div>
        </td>
        <td class="text-muted small" style="white-space:nowrap;">${r.opened || ''}</td>
        <td style="white-space:nowrap;">${chip(r.severity || '', sevTone)}</td>
        <td class="text-right">${actionBtn(r.href, r.cta || 'View')}</td>
      </tr>
    `;
  }).join('');

  const remindersRows = reminders.map((r) => {
    const channel = (r.channel || '').toLowerCase();
    const chTone = channel.includes('sms') ? 'blue' : 'gray';
    return `
      <tr>
        <td>
          <div class="font-weight-bold">${r.reminder || ''}</div>
          <div class="text-muted small">To ${r.recipient || ''} ${chip(r.channel || '', chTone)}</div>
        </td>
        <td class="text-muted small" style="white-space:nowrap;">${r.scheduled || ''}</td>
        <td class="text-right">${actionBtn(r.href, r.cta || 'Open')}</td>
      </tr>
    `;
  }).join('');

  container.innerHTML =
    tableWrap('approvals', 'Pending approvals', 'fe-check-square', approvalsRows) +
    tableWrap('issues', 'Issues reported', 'fe-alert-triangle', issuesRows) +
    tableWrap('reminders', 'Automated reminders', 'fe-bell', remindersRows);
}

function dashboardRenderActivity(items) {
  const container = document.getElementById('dashboard-activity');
  if (!container) return;

  if (!items || !items.length) {
    container.innerHTML = '<div class="text-muted">No recent activity</div>';
    return;
  }

  const iconFor = (type) => {
    if (type === 'staff') return 'fe-user';
    if (type === 'location') return 'fe-map-pin';
    return 'fe-activity';
  };

  container.innerHTML = '';
  items.forEach((it) => {
    const row = document.createElement('div');
    row.className = 'dashboard-activity-item';

    const icon = document.createElement('div');
    icon.className = 'text-muted';
    icon.innerHTML = `<i class="fe ${iconFor(it.type)}"></i>`;

    const body = document.createElement('div');
    const title = document.createElement('div');
    title.className = 'font-weight-bold';
    title.textContent = it.title || '';
    const detail = document.createElement('div');
    detail.className = 'text-muted small';
    detail.textContent = it.detail || '';

    body.appendChild(title);
    body.appendChild(detail);

    row.appendChild(icon);
    row.appendChild(body);

    container.appendChild(row);
  });
}

function dashboardSetActiveDaysButton(days) {
  $('.dashboard-days').removeClass('dashboard-btn-active');
  $(`.dashboard-days[data-days="${days}"]`).addClass('dashboard-btn-active');
}

function dashboardFetchAndRender(cfg) {
  const locationId = dashboardGetLocationIdFromUrl();
  const params = new URLSearchParams();
  params.set('days', `${cfg.days}`);
  if (locationId) params.set('location_id', locationId);

  dashboardSetText('dashboard-scope', `Last ${cfg.days} days`);
  $('#dashboard-activity').html('<div class="text-muted">Loading…</div>');
  $('#dashboard-action-center').html('<div class="text-muted">Loading…</div>');
  dashboardSetText('chart-new-customers-total', '—');
  dashboardSetText('chart-new-customers-sub', `New customers in last ${cfg.days} days`);
  dashboardSetText('revenue-total', '—');
  dashboardSetText('revenue-sub', 'Revenue in selected period');

  return fetch(`/administration/dashboard/data/?${params.toString()}`, {
    credentials: 'same-origin',
    headers: { 'Accept': 'application/json' },
  })
    .then((r) => r.json())
    .then((payload) => {
      if (payload && payload.kpi) {
        dashboardSetText('kpi-customers', `${payload.kpi.customers}`);
        dashboardSetText('kpi-staff', `${payload.kpi.staff}`);
        dashboardSetText('kpi-locations', `${payload.kpi.locations}`);
        dashboardSetText('kpi-rooms', `${payload.kpi.rooms}`);
      }

      dashboardRenderChartNewCustomers(payload && payload.charts ? payload.charts.new_customers : null);
      dashboardRenderActivity(payload && payload.activity ? payload.activity : []);
      dashboardRenderRevenue(payload && payload.revenue ? payload.revenue : null, cfg.days);
      dashboardRenderActionCenter(payload && payload.action_center ? payload.action_center : null);

      const updatedEl = document.getElementById('dashboard-activity-updated');
      if (updatedEl) updatedEl.textContent = dashboardFormatUpdatedAgo(new Date());
    })
    .catch(() => {
      $('#dashboard-activity').html('<div class="text-danger">Failed to load dashboard data</div>');
      $('#dashboard-action-center').html('<div class="text-danger">Failed to load dashboard data</div>');
      dashboardRenderRevenue(null, cfg.days);
      dashboardRenderActionCenter(null);
    });
}

$(document).ready(function () {
  const cfg = dashboardLoadConfig();

  dashboardApplyWidgetOrder(cfg);
  dashboardApplyWidgetVisibility(cfg);
  dashboardSetActiveDaysButton(cfg.days);

  dashboardFetchAndRender(cfg);

  $('.dashboard-days').on('click', function () {
    const days = parseInt($(this).attr('data-days'), 10);
    if (!days) return;
    cfg.days = days;
    dashboardSaveConfig(cfg);
    dashboardSetActiveDaysButton(cfg.days);
    dashboardFetchAndRender(cfg);
  });

  $('#dashboard-refresh').on('click', function () {
    dashboardFetchAndRender(cfg);
  });

  $('#dashboard-reset').on('click', function () {
    const next = dashboardGetDefaultConfig();
    dashboardSaveConfig(next);
    window.location.reload();
  });

  let isEditing = false;
  $('#dashboard-edit-toggle').on('click', function () {
    isEditing = !isEditing;
    if (isEditing) {
      $(this).addClass('dashboard-btn-active');
      $(this).html('<i class="fe fe-check mr-2"></i>Done');
      dashboardEnableInlineEditMode(cfg);
    } else {
      $(this).removeClass('dashboard-btn-active');
      $(this).html('<i class="fe fe-edit-3 mr-2"></i>Edit layout');
      dashboardDisableInlineEditMode();
    }
  });
});
