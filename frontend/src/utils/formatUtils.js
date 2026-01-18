/**
 * Global Format Utilities
 * 
 * Standards:
 * - Time Zone: India Standard Time (IST), GMT +5:30
 * - Date Format: DD/MM/YYYY
 * - Time Format: 24-hour (HH:mm)
 * - Currency: Indian Rupee (₹)
 */

// IST offset in milliseconds (+5:30 = 5.5 hours)
const IST_OFFSET = 5.5 * 60 * 60 * 1000;

/**
 * Convert any date to IST
 */
export const toIST = (date) => {
  const d = new Date(date);
  // Get UTC time
  const utc = d.getTime() + (d.getTimezoneOffset() * 60000);
  // Add IST offset
  return new Date(utc + IST_OFFSET);
};

/**
 * Get current date/time in IST
 */
export const nowIST = () => toIST(new Date());

/**
 * Format date as DD/MM/YYYY
 */
export const formatDate = (date) => {
  if (!date) return '';
  const d = toIST(date);
  const day = String(d.getDate()).padStart(2, '0');
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const year = d.getFullYear();
  return `${day}/${month}/${year}`;
};

/**
 * Format date with weekday: Mon, 18/01/2026
 */
export const formatDateWithDay = (date) => {
  if (!date) return '';
  const d = toIST(date);
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const day = String(d.getDate()).padStart(2, '0');
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const year = d.getFullYear();
  return `${days[d.getDay()]}, ${day}/${month}/${year}`;
};

/**
 * Format date long: Monday, 18 January 2026
 */
export const formatDateLong = (date) => {
  if (!date) return '';
  const d = toIST(date);
  const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const months = ['January', 'February', 'March', 'April', 'May', 'June', 
                  'July', 'August', 'September', 'October', 'November', 'December'];
  return `${days[d.getDay()]}, ${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
};

/**
 * Format time as HH:mm (24-hour)
 */
export const formatTime = (date) => {
  if (!date) return '';
  const d = toIST(date);
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
};

/**
 * Format datetime as DD/MM/YYYY HH:mm
 */
export const formatDateTime = (date) => {
  if (!date) return '';
  return `${formatDate(date)} ${formatTime(date)}`;
};

/**
 * Format datetime for display with day: Mon, 18/01/2026 14:30
 */
export const formatDateTimeWithDay = (date) => {
  if (!date) return '';
  return `${formatDateWithDay(date)} ${formatTime(date)}`;
};

/**
 * Get relative date label: Today, Tomorrow, or formatted date
 */
export const getRelativeDate = (date) => {
  if (!date) return '';
  const d = toIST(date);
  const today = nowIST();
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  
  if (d.toDateString() === today.toDateString()) return 'Today';
  if (d.toDateString() === tomorrow.toDateString()) return 'Tomorrow';
  return formatDateWithDay(date);
};

/**
 * Format time range: HH:mm - HH:mm
 */
export const formatTimeRange = (startDate, endDate) => {
  return `${formatTime(startDate)} - ${formatTime(endDate)}`;
};

/**
 * Format currency in INR: ₹1,234.56
 */
export const formatCurrency = (amount) => {
  if (amount === null || amount === undefined) return '₹0';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
};

/**
 * Format currency without decimals: ₹1,234
 */
export const formatCurrencyWhole = (amount) => {
  if (amount === null || amount === undefined) return '₹0';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

/**
 * Get today's date in YYYY-MM-DD format for input[type="date"]
 */
export const getTodayInputFormat = () => {
  const d = nowIST();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

/**
 * Convert datetime-local input value to IST ISO string for API
 */
export const inputToISTISO = (inputValue) => {
  if (!inputValue) return null;
  // Input is already in local format, treat it as IST
  const d = new Date(inputValue);
  return d.toISOString();
};

/**
 * Convert ISO date to datetime-local input format
 */
export const isoToInputFormat = (isoString) => {
  if (!isoString) return '';
  const d = toIST(isoString);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}`;
};

/**
 * Parse DD/MM/YYYY string to Date
 */
export const parseDate = (dateString) => {
  if (!dateString) return null;
  const [day, month, year] = dateString.split('/').map(Number);
  return new Date(year, month - 1, day);
};

/**
 * Get time until a date in human readable format
 */
export const getTimeUntil = (date) => {
  const now = nowIST();
  const target = toIST(date);
  const diff = target - now;
  
  if (diff < 0) return 'Started';
  
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  
  if (hours > 24) {
    const days = Math.floor(hours / 24);
    return `in ${days} day${days > 1 ? 's' : ''}`;
  }
  if (hours > 0) return `in ${hours}h ${minutes}m`;
  return `in ${minutes}m`;
};

/**
 * Format date for grouping headers: Monday, 18 January 2026
 */
export const formatGroupDate = (date) => {
  return formatDateLong(date);
};

// Export constants for reference
export const TIMEZONE = 'IST (GMT +5:30)';
export const DATE_FORMAT = 'DD/MM/YYYY';
export const TIME_FORMAT = 'HH:mm';
export const CURRENCY = 'INR';
export const CURRENCY_SYMBOL = '₹';
