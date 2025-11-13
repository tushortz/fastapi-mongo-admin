/**
 * Analytics view component
 * @module react/components/AnalyticsView
 */

import { getAnalytics, getSchema } from '../services/api.js';
import { titleize } from '../utils.js';
import { useTranslation } from '../hooks/useTranslation.js';

const { useState, useRef, useEffect } = React;

/**
 * Analytics view component
 * @param {Object} props - Component props
 */
export function AnalyticsView({ collection }) {
  const [field, setField] = useState('');
  const [groupBy, setGroupBy] = useState('');
  const [aggregation, setAggregation] = useState('count');
  const [chartType, setChartType] = useState('bar');
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [availableFields, setAvailableFields] = useState([]);
  const chartRef = useRef(null);
  const chartInstanceRef = useRef(null);
  const t = useTranslation();

  // Load schema to get available fields
  useEffect(() => {
    if (collection) {
      loadSchema();
    }
  }, [collection]);

  // Cleanup chart on unmount
  useEffect(() => {
    return () => {
      if (chartInstanceRef.current) {
        try {
          chartInstanceRef.current.destroy();
        } catch (e) {
          // Ignore errors during unmount cleanup
        }
        chartInstanceRef.current = null;
      }
    };
  }, []);

  // Regenerate chart when chart type, data, or aggregation changes
  useEffect(() => {
    if (chartData && chartData.data && chartData.data.length > 0) {
      // Small delay to ensure canvas is ready
      const timer = setTimeout(() => {
        // Check if component is still mounted and refs are valid
        if (!chartRef.current) {
          return;
        }

        const Chart = window.Chart;
        if (!Chart) {
          setError(t('analytics.chartNotLoaded'));
          setLoading(false);
          return;
        }

        // Destroy existing chart safely
        if (chartInstanceRef.current) {
          try {
            chartInstanceRef.current.destroy();
          } catch (e) {
            // Chart might already be destroyed, ignore error
          }
          chartInstanceRef.current = null;
        }

        // Double-check ref is still valid after async operations
        if (!chartRef.current) {
          return;
        }

        try {
          const ctx = chartRef.current.getContext('2d');
          if (!ctx) {
            setError(t('analytics.failedToCreateChart', { error: 'Could not initialize chart canvas' }));
            setLoading(false);
            return;
          }

          // Handle API response structure: data array with {label, data} objects
          const labels = chartData.data.map(item =>
            String(item.label || item.group || item._id || item.value || 'Unknown')
          );
          const values = chartData.data.map(item => {
            // API returns {label: "...", data: number} structure
            if (item.data !== undefined) {
              return Number(item.data) || 0;
            }
            // Fallback to other possible property names
            return Number(item[aggregation] || item.value || item.count || item.total || 0);
          });

          // Build chart title
          const aggregationLabel = t(`analytics.${aggregation}`) || (aggregation.charAt(0).toUpperCase() + aggregation.slice(1));
          const fieldLabel = titleize(field);
          let chartTitle = `${aggregationLabel} of ${fieldLabel}`;
          if (groupBy) {
            const groupByLabel = titleize(groupBy);
            chartTitle += ` ${t('analytics.by')} ${groupByLabel}`;
          }

          chartInstanceRef.current = new Chart(ctx, {
            type: chartType,
            data: {
              labels,
              datasets: [{
                label: aggregationLabel,
                data: values,
                backgroundColor: chartType === 'pie' || chartType === 'doughnut'
                  ? [
                      'rgba(59, 130, 246, 0.8)',
                      'rgba(16, 185, 129, 0.8)',
                      'rgba(245, 158, 11, 0.8)',
                      'rgba(239, 68, 68, 0.8)',
                      'rgba(139, 92, 246, 0.8)',
                      'rgba(236, 72, 153, 0.8)',
                    ]
                  : 'rgba(59, 130, 246, 0.8)',
                borderColor: chartType === 'pie' || chartType === 'doughnut'
                  ? [
                      'rgba(59, 130, 246, 1)',
                      'rgba(16, 185, 129, 1)',
                      'rgba(245, 158, 11, 1)',
                      'rgba(239, 68, 68, 1)',
                      'rgba(139, 92, 246, 1)',
                      'rgba(236, 72, 153, 1)',
                    ]
                  : 'rgba(59, 130, 246, 1)',
                borderWidth: 1,
              }],
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                title: {
                  display: true,
                  text: chartTitle,
                  font: {
                    size: 16,
                    weight: 'bold',
                  },
                  padding: {
                    top: 10,
                    bottom: 20,
                  },
                },
                legend: {
                  display: true,
                  position: chartType === 'pie' || chartType === 'doughnut' ? 'right' : 'top',
                  labels: {
                    font: {
                      size: 12,
                    },
                    padding: 15,
                    usePointStyle: true,
                  },
                },
              },
              scales: chartType === 'line' || chartType === 'bar' ? {
                y: {
                  beginAtZero: true,
                  title: {
                    display: true,
                    text: aggregationLabel,
                    font: {
                      size: 12,
                      weight: 'bold',
                    },
                  },
                },
                x: {
                  title: {
                    display: true,
                    text: groupBy ? titleize(groupBy) : fieldLabel,
                    font: {
                      size: 12,
                      weight: 'bold',
                    },
                  },
                },
              } : undefined,
            },
          });
          setLoading(false);
          setError('');
        } catch (err) {
          // Only set error if component is still mounted
          if (chartRef.current) {
            setError(t('analytics.failedToCreateChart', { error: err.message }));
            setLoading(false);
          }
        }
      }, 100);

      return () => {
        clearTimeout(timer);
        // Clean up chart if component unmounts or dependencies change
        if (chartInstanceRef.current) {
          try {
            chartInstanceRef.current.destroy();
          } catch (e) {
            // Ignore errors during cleanup
          }
          chartInstanceRef.current = null;
        }
      };
    } else {
      // Clean up chart when chartData is cleared
      if (chartInstanceRef.current) {
        try {
          chartInstanceRef.current.destroy();
        } catch (e) {
          // Ignore errors during cleanup
        }
        chartInstanceRef.current = null;
      }
    }
  }, [chartType, chartData, aggregation, field, groupBy, t]);

  const loadSchema = async () => {
    if (!collection) return;
    try {
      const schemaData = await getSchema(collection);
      // Convert fields object to array
      const fieldsObj = schemaData?.fields || {};
      const fields = Array.isArray(fieldsObj)
        ? fieldsObj.map(f => typeof f === 'string' ? f : (f.name || f))
        : Object.keys(fieldsObj);
      setAvailableFields(fields);
    } catch (err) {
      // If schema fails, try to get fields from documents
      setAvailableFields([]);
    }
  };

  const loadAnalytics = async () => {
    if (!field || !collection) {
      setError(t('analytics.selectField'));
      return;
    }

    setLoading(true);
    setError('');

    try {
      const params = { field, aggregation_type: aggregation };
      if (groupBy) params.group_by = groupBy;

      const data = await getAnalytics(collection, params);

      if (!data || !data.data || data.data.length === 0) {
        setError(t('analytics.noData'));
        setChartData(null);
        setLoading(false);
        return;
      }

      // Check if Chart.js is available
      const Chart = window.Chart;
      if (!Chart) {
        setError(t('analytics.chartNotLoaded'));
        setLoading(false);
        return;
      }

      setChartData(data);
    } catch (err) {
      setError(err.message || t('analytics.failedToLoad'));
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="bg-white rounded-lg shadow p-6 mb-5 flex-shrink-0">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">{t('analytics.title')}</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">{t('analytics.fieldToPlot')}</label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white"
              value={field}
              onChange={(e) => setField(e.target.value)}>
              <option value="">{t('common.selectField')}</option>
              {[...availableFields].sort((a, b) => {
                const aStr = titleize(a).toLowerCase();
                const bStr = titleize(b).toLowerCase();
                return aStr.localeCompare(bStr);
              }).map((fieldName) => (
                <option key={fieldName} value={fieldName}>
                  {titleize(fieldName)}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('analytics.groupBy')}
            </label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white"
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value)}>
              <option value="">{t('common.none')}</option>
              {[...availableFields].sort((a, b) => {
                const aStr = titleize(a).toLowerCase();
                const bStr = titleize(b).toLowerCase();
                return aStr.localeCompare(bStr);
              }).map((fieldName) => (
                <option key={fieldName} value={fieldName}>
                  {titleize(fieldName)}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('analytics.aggregationType')}
            </label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white"
              value={aggregation}
              onChange={(e) => setAggregation(e.target.value)}>
              <option value="avg">{t('analytics.average')}</option>
              <option value="count">{t('analytics.count')}</option>
              <option value="max">{t('analytics.maximum')}</option>
              <option value="min">{t('analytics.minimum')}</option>
              <option value="sum">{t('analytics.sum')}</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">{t('analytics.chartType')}</label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white"
              value={chartType}
              onChange={(e) => setChartType(e.target.value)}>
              <option value="bar">{t('analytics.barChart')}</option>
              <option value="doughnut">{t('analytics.doughnutChart')}</option>
              <option value="line">{t('analytics.lineChart')}</option>
              <option value="pie">{t('analytics.pieChart')}</option>
            </select>
          </div>
        </div>
        {error && (
          <div className="mb-4 p-3 rounded bg-red-100 text-red-800 text-sm">{error}</div>
        )}
        <button
          onClick={loadAnalytics}
          disabled={loading || !field}
          className="px-5 py-2.5 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
          {loading ? t('common.generating') : t('analytics.generateChart')}
        </button>
      </div>
      {chartData && chartData.data && chartData.data.length > 0 && (
        <div className="flex-1 bg-white rounded-lg shadow p-6 overflow-hidden">
          <div className="h-full" style={{ minHeight: '400px', position: 'relative' }}>
            <canvas ref={chartRef} style={{ maxHeight: '100%' }}></canvas>
          </div>
        </div>
      )}
    </div>
  );
}
