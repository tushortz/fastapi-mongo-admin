/**
 * Date hierarchy navigation component
 * @module react/components/DateHierarchy
 */

import { useTranslation } from '../hooks/useTranslation.js';

const { useState, useEffect } = React;

/**
 * Date hierarchy component for navigating by year/month/day
 * @param {Object} props - Component props
 */
export function DateHierarchy({ fieldName, onDateSelect, currentDate = null }) {
  const [selectedYear, setSelectedYear] = useState(null);
  const [selectedMonth, setSelectedMonth] = useState(null);
  const [selectedDay, setSelectedDay] = useState(null);
  const [availableYears, setAvailableYears] = useState([]);
  const [availableMonths, setAvailableMonths] = useState([]);
  const [availableDays, setAvailableDays] = useState([]);
  const t = useTranslation();

  useEffect(() => {
    if (currentDate) {
      const date = new Date(currentDate);
      if (!isNaN(date.getTime())) {
        setSelectedYear(date.getFullYear());
        setSelectedMonth(date.getMonth() + 1);
        setSelectedDay(date.getDate());
      }
    }
  }, [currentDate]);

  // Generate years (last 10 years + current year)
  useEffect(() => {
    const years = [];
    const currentYear = new Date().getFullYear();
    for (let i = 0; i <= 10; i++) {
      years.push(currentYear - i);
    }
    setAvailableYears(years);
  }, []);

  // Generate months when year is selected
  useEffect(() => {
    if (selectedYear) {
      const months = [];
      for (let i = 1; i <= 12; i++) {
        months.push(i);
      }
      setAvailableMonths(months);
    } else {
      setAvailableMonths([]);
    }
  }, [selectedYear]);

  // Generate days when month is selected
  useEffect(() => {
    if (selectedYear && selectedMonth) {
      const daysInMonth = new Date(selectedYear, selectedMonth, 0).getDate();
      const days = [];
      for (let i = 1; i <= daysInMonth; i++) {
        days.push(i);
      }
      setAvailableDays(days);
    } else {
      setAvailableDays([]);
    }
  }, [selectedYear, selectedMonth]);

  const handleYearChange = (year) => {
    setSelectedYear(year);
    setSelectedMonth(null);
    setSelectedDay(null);
    if (year && onDateSelect) {
      // Select entire year
      const startDate = new Date(year, 0, 1);
      const endDate = new Date(year, 11, 31, 23, 59, 59, 999);
      onDateSelect({
        $gte: startDate.toISOString(),
        $lte: endDate.toISOString()
      });
    }
  };

  const handleMonthChange = (month) => {
    setSelectedMonth(month);
    setSelectedDay(null);
    if (selectedYear && month && onDateSelect) {
      // Select entire month
      const startDate = new Date(selectedYear, month - 1, 1);
      const endDate = new Date(selectedYear, month, 0, 23, 59, 59, 999);
      onDateSelect({
        $gte: startDate.toISOString(),
        $lte: endDate.toISOString()
      });
    }
  };

  const handleDayChange = (day) => {
    setSelectedDay(day);
    if (selectedYear && selectedMonth && day && onDateSelect) {
      // Select specific day
      const startDate = new Date(selectedYear, selectedMonth - 1, day, 0, 0, 0, 0);
      const endDate = new Date(selectedYear, selectedMonth - 1, day, 23, 59, 59, 999);
      onDateSelect({
        $gte: startDate.toISOString(),
        $lte: endDate.toISOString()
      });
    }
  };

  const monthNames = [
    t('date.january') || 'January',
    t('date.february') || 'February',
    t('date.march') || 'March',
    t('date.april') || 'April',
    t('date.may') || 'May',
    t('date.june') || 'June',
    t('date.july') || 'July',
    t('date.august') || 'August',
    t('date.september') || 'September',
    t('date.october') || 'October',
    t('date.november') || 'November',
    t('date.december') || 'December'
  ];

  const clearSelection = () => {
    setSelectedYear(null);
    setSelectedMonth(null);
    setSelectedDay(null);
    if (onDateSelect) {
      onDateSelect(null);
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-gray-700">
          {t('date.hierarchy') || 'Date Hierarchy'} - {fieldName}
        </h4>
        {(selectedYear || selectedMonth || selectedDay) && (
          <button
            onClick={clearSelection}
            className="text-xs text-gray-500 hover:text-gray-700">
            {t('common.clear') || 'Clear'}
          </button>
        )}
      </div>

      <div className="space-y-3">
        <div className="flex flex-col gap-2">
          {/* Year Selector */}
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white text-gray-900"
            value={selectedYear || ''}
            onChange={(e) => handleYearChange(e.target.value ? parseInt(e.target.value) : null)}>
            <option value="">{t('date.selectYear') || 'Select Year'}</option>
            {availableYears.map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>

          {/* Month Selector */}
          {selectedYear && (
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white text-gray-900"
              value={selectedMonth || ''}
              onChange={(e) => handleMonthChange(e.target.value ? parseInt(e.target.value) : null)}>
              <option value="">{t('date.selectMonth') || 'Select Month'}</option>
              {availableMonths.map(month => (
                <option key={month} value={month}>{monthNames[month - 1]}</option>
              ))}
            </select>
          )}

          {/* Day Selector */}
          {selectedYear && selectedMonth && (
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white text-gray-900"
              value={selectedDay || ''}
              onChange={(e) => handleDayChange(e.target.value ? parseInt(e.target.value) : null)}>
              <option value="">{t('date.selectDay') || 'Select Day'}</option>
              {availableDays.map(day => (
                <option key={day} value={day}>{day}</option>
              ))}
            </select>
          )}
        </div>

        {/* Breadcrumb */}
        {(selectedYear || selectedMonth || selectedDay) && (
          <div className="flex items-center gap-1 text-sm text-gray-600 pt-2 border-t border-gray-200">
            {selectedYear && (
              <>
                <button
                  onClick={() => handleYearChange(selectedYear)}
                  className="hover:text-blue-600">
                  {selectedYear}
                </button>
                {selectedMonth && (
                  <>
                    <span>/</span>
                    <button
                      onClick={() => handleMonthChange(selectedMonth)}
                      className="hover:text-blue-600">
                      {monthNames[selectedMonth - 1]}
                    </button>
                    {selectedDay && (
                      <>
                        <span>/</span>
                        <span>{selectedDay}</span>
                      </>
                    )}
                  </>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

