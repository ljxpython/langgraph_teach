import { createContext } from 'react';
import { TabVisibilityContextType } from './types';
// @ts-expect-error  MC8yOmFIVnBZMlhtblk3a3ZiUG1yS002WkRNd1Z3PT06N2NlM2I5OTU=

// Default context value
const defaultContext: TabVisibilityContextType = {
  visibleTabs: {},
  setTabVisibility: () => {},
  isTabVisible: () => false,
};

// Create the context
export const TabVisibilityContext = createContext<TabVisibilityContextType>(defaultContext);
// NOTE  MS8yOmFIVnBZMlhtblk3a3ZiUG1yS002WkRNd1Z3PT06N2NlM2I5OTU=
