import { track } from '@vercel/analytics/react';

// Vercel Analytics automatically initialises when the <Analytics /> component is mounted.
export const initAnalytics = () => true;

export const analyticsEnabled = () => typeof window !== 'undefined';

export const trackPageview = (page) => {
  if (typeof window === 'undefined' || !page) return;
  track('pageview', { page });
};

export const trackEvent = ({ category, action, label, value }) => {
  if (typeof window === 'undefined' || !action) return;
  const payload = {};
  if (category) payload.category = category;
  if (label) payload.label = label;
  if (typeof value !== 'undefined') payload.value = value;
  track(action, payload);
};

export const resetAnalyticsForTests = () => true;
