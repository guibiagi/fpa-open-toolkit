/**
 * FP&A Open Toolkit — Chart.js Helpers
 * Reusable helpers for initializing charts with project defaults.
 */

(function(window) {
  'use strict';

  const FPA_COLORS = {
    primary:   '#059669',
    secondary: '#2563eb',
    danger:    '#dc2626',
    warning:   '#f59e0b',
    info:      '#6366f1',
    slate:     '#64748b',
    slateLight:'#94a3b8',
    grid:      '#e2e8f0'
  };

  const COMMON_OPTIONS = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false
    },
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          usePointStyle: true,
          padding: 20,
          font: { family: "'Inter', ui-sans-serif, system-ui", size: 12 }
        }
      },
      tooltip: {
        backgroundColor: '#1e293b',
        titleFont: { family: "'Inter', ui-sans-serif, system-ui", size: 13 },
        bodyFont:  { family: "'Inter', ui-sans-serif, system-ui", size: 12 },
        padding: 12,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {}
      }
    },
    scales: {
      x: {
        grid: { color: FPA_COLORS.grid, drawBorder: false },
        ticks: {
          font: { family: "'Inter', ui-sans-serif, system-ui", size: 11 },
          color: FPA_COLORS.slate
        }
      },
      y: {
        grid: { color: FPA_COLORS.grid, drawBorder: false },
        ticks: {
          font: { family: "'Inter', ui-sans-serif, system-ui", size: 11 },
          color: FPA_COLORS.slate,
          callback: function(value) {
            // Format BRL-k
            if (Math.abs(value) >= 1e6) return 'R$ ' + (value/1e6).toFixed(1) + 'M';
            if (Math.abs(value) >= 1e3) return 'R$ ' + (value/1e3).toFixed(0) + 'k';
            return 'R$ ' + value;
          }
        }
      }
    }
  };

  /**
   * Render a line chart.
   *
   * @param {HTMLCanvasElement} ctx     Target canvas
   * @param {string[]}          labels  X-axis labels
   * @param {Object[]}          datasets Chart.js dataset objects
   */
  function renderLineChart(ctx, labels, datasets) {
    if (!ctx) return null;
    return new Chart(ctx, {
      type: 'line',
      data: { labels: labels, datasets: datasets },
      options: COMMON_OPTIONS
    });
  }

  /**
   * Render a donut chart.
   *
   * @param {HTMLCanvasElement} ctx    Target canvas
   * @param {string[]}          labels Slice labels
   * @param {number[]}          values Slice values
   * @param {string[]}          [colors] Optional custom colors
   */
  function renderDonutChart(ctx, labels, values, colors) {
    if (!ctx) return null;
    const palette = colors || [
      FPA_COLORS.primary, FPA_COLORS.secondary, FPA_COLORS.warning,
      FPA_COLORS.danger, FPA_COLORS.info, FPA_COLORS.slate
    ];
    return new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: palette,
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '60%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              usePointStyle: true,
              padding: 16,
              font: { family: "'Inter', ui-sans-serif, system-ui", size: 12 }
            }
          },
          tooltip: {
            backgroundColor: '#1e293b',
            callbacks: {
              label: function(context) {
                const val = context.parsed;
                const total = context.dataset.data.reduce((a,b) => a+b, 0);
                const pct = ((val / total) * 100).toFixed(1);
                return `${context.label}: ${val.toLocaleString('pt-BR')} (${pct}%)`;
              }
            }
          }
        }
      }
    });
  }

  /**
   * Render a bar chart.
   *
   * @param {HTMLCanvasElement} ctx
   * @param {string[]} labels
   * @param {Object[]} datasets
   */
  function renderBarChart(ctx, labels, datasets) {
    if (!ctx) return null;
    return new Chart(ctx, {
      type: 'bar',
      data: { labels: labels, datasets: datasets },
      options: {
        ...COMMON_OPTIONS,
        scales: {
          x: COMMON_OPTIONS.scales.x,
          y: {
            ...COMMON_OPTIONS.scales.y,
            beginAtZero: true
          }
        }
      }
    });
  }

  // Expose globally
  window.renderLineChart = renderLineChart;
  window.renderDonutChart = renderDonutChart;
  window.renderBarChart = renderBarChart;
  window.FPA_COLORS = FPA_COLORS;

})(window);
