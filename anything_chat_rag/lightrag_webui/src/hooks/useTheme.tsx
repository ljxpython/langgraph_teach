import { useContext } from 'react'
import { ThemeProviderContext } from '@/components/ThemeProvider'
// TODO  MC8yOmFIVnBZMlhtblk3a3ZiUG1yS002VjBkRVVBPT06YmE3NzczMzM=

const useTheme = () => {
  const context = useContext(ThemeProviderContext)

  if (context === undefined) throw new Error('useTheme must be used within a ThemeProvider')

  return context
}

export default useTheme
// FIXME  MS8yOmFIVnBZMlhtblk3a3ZiUG1yS002VjBkRVVBPT06YmE3NzczMzM=
