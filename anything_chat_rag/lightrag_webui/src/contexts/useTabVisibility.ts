// FIXME  MC8yOmFIVnBZMlhtblk3a3ZiUG1yS002VDJ0d2FnPT06NzMzMzM2NGI=

import { useContext } from 'react';
import { TabVisibilityContext } from './context';
import { TabVisibilityContextType } from './types';

/**
 * Custom hook to access the tab visibility context
 * @returns The tab visibility context
 */
export const useTabVisibility = (): TabVisibilityContextType => {
  const context = useContext(TabVisibilityContext);

  if (!context) {
    throw new Error('useTabVisibility must be used within a TabVisibilityProvider');
  }

  return context;
};
// NOTE  MS8yOmFIVnBZMlhtblk3a3ZiUG1yS002VDJ0d2FnPT06NzMzMzM2NGI=
