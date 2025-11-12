/**
 * Analytics view component
 * @module react/components/AnalyticsView
 */

import { getAnalytics, getSchema } from '../services/api.js';
import { titleize } from '../utils.js';

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
        chartInstanceRef.current.destroy();
      }
    };
  }, []);

  // Regenerate chart when chart type, data, or aggregation changes
  useEffect(() => {
    if (chartData && chartData.data && chartData.data.length > 0) {
      // Small delay to ensure canvas is ready
      const timer = setTimeout(() => {
        const Chart = window.Chart;
        if (!Chart) {
          setError('Chart.js library is not loaded. Please refresh the page.');
          setLoading(false);
          return;
        }

        if (!chartRef.current) {
          setLoading(false);
          return;
        }

        // Destroy existing chart
        if (chartInstanceRef.current) {
          chartInstanceRef.current.destroy();
          chartInstanceRef.current = null;
        }

        try {
          const ctx = chartRef.current.getContext('2d');
          if (!ctx) {
            setError('Could not initialize chart canvas');
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
          const aggregationLabel = aggregation.charAt(0).toUpperCase() + aggregation.slice(1);
          const fieldLabel = titleize(field);
          let chartTitle = `${aggregationLabel} of ${fieldLabel}`;
          if (groupBy) {
            const groupByLabel = titleize(groupBy);
            chartTitle += ` by ${groupByLabel}`;
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
          setError(`Failed to create chart: ${err.message}`);
          setLoading(false);
        }
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [chartType, chartData, aggregation, field, groupBy]);

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
      setError('Please select a field to plot');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const params = { field, aggregation_type: aggregation };
      if (groupBy) params.group_by = groupBy;

      const data = await getAnalytics(collection, params);

      if (!data || !data.data || data.data.length === 0) {
        setError('No data available for the selected field');
        setChartData(null);
        setLoading(false);
        return;
      }

      // Check if Chart.js is available
      const Chart = window.Chart;
      if (!Chart) {
        setError('Chart.js library is not loaded. Please refresh the page.');
        setLoading(false);
        return;
      }

      setChartData(data);
    } catch (err) {
      setError(err.message || 'Failed to load analytics');
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="bg-white rounded-lg shadow p-6 mb-5 flex-shrink-0">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Analytics Configuration</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Field to Plot</label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white"
              value={field}
              onChange={(e) => setField(e.target.value)}>
              <option value="">Select field...</option>
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
              Group By (Optional)
            </label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white"
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value)}>
              <option value="">None</option>
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
              Aggregation Type
            </label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white"
              value={aggregation}
              onChange={(e) => setAggregation(e.target.value)}>
              <option value="avg">Average</option>
              <option value="count">Count</option>
              <option value="max">Maximum</option>
              <option value="min">Minimum</option>
              <option value="sum">Sum</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Chart Type</label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white"
              value={chartType}
              onChange={(e) => setChartType(e.target.value)}>
              <option value="bar">Bar Chart</option>
              <option value="doughnut">Doughnut Chart</option>
              <option value="line">Line Chart</option>
              <option value="pie">Pie Chart</option>
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
          {loading ? 'Generating...' : 'Generate Chart'}
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
