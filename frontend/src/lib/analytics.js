import ReactGA from 'react-ga4';

let isInitialized = false;

export const initAnalytics = (measurementId) => {
  if (measurementId && !isInitialized) {
    ReactGA.initialize(measurementId);
    isInitialized = true;
  }
  return isInitialized;
};

export const analyticsEnabled = () => isInitialized;

export const trackPageview = (page) => {
  if (!isInitialized) return;
  ReactGA.send({ hitType: 'pageview', page });
};

export const trackEvent = ({ category, action, label, value }) => {
  if (!isInitialized) return;
  ReactGA.event({ category, action, label, value });
};

export const resetAnalyticsForTests = () => {
  // Exposed for unit-test environments if needed.
  isInitialized = false;
};
