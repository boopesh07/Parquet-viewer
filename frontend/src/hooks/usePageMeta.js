import { useEffect } from 'react';

const ensureMetaTag = (name) => {
  let element = document.querySelector(`meta[name="${name}"]`);
  if (!element) {
    element = document.createElement('meta');
    element.setAttribute('name', name);
    document.head.appendChild(element);
  }
  return element;
};

export function usePageMeta({ title, description, keywords }) {
  useEffect(() => {
    if (title) {
      document.title = title;
    }

    if (description) {
      const descTag = ensureMetaTag('description');
      descTag.setAttribute('content', description);
    }

    if (keywords && keywords.length) {
      const keywordTag = ensureMetaTag('keywords');
      keywordTag.setAttribute('content', keywords.join(', '));
    }
  }, [title, description, keywords && keywords.join(',')]);
}
