
const DASHBOARD_STORAGE_KEY = 'ruoom.dashboard.v1';

function dashboardGetLocationIdFromUrl() {
  const url = new URL(window.location.href);
  return url.searchParams.get('location_id');
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

function dashboardRenderChartNewCustomers(data) {
  const canvas = document.getElementById('chart-new-customers');
  if (!canvas || !data) return;

  const labels = data.labels || [];
  const series = data.series || [];

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
  dashboardSetText('chart-new-customers-total', '—');
  dashboardSetText('chart-new-customers-sub', `New customers in last ${cfg.days} days`);

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

      const updatedEl = document.getElementById('dashboard-activity-updated');
      if (updatedEl) updatedEl.textContent = dashboardFormatUpdatedAgo(new Date());
    })
    .catch(() => {
      $('#dashboard-activity').html('<div class="text-danger">Failed to load dashboard data</div>');
    });
}

$(document).ready(function () {
  const cfg = dashboardLoadConfig();

  dashboardApplyWidgetOrder(cfg);
  dashboardApplyWidgetVisibility(cfg);
  dashboardRenderCustomizeList(cfg);
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

  $('#dashboardCustomizeModal').on('show.bs.modal', function () {
    dashboardRenderCustomizeList(cfg);
  });
});
