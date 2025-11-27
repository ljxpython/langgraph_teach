// FIXME  MC8yOmFIVnBZMlhtblk3a3ZiUG1yS002VUcxcFp3PT06N2Q1NmQyMmE=

import Button from '@/components/ui/Button'
import useTheme from '@/hooks/useTheme'
import { MoonIcon, SunIcon } from 'lucide-react'
import { useCallback } from 'react'
import { controlButtonVariant } from '@/lib/constants'
import { useTranslation } from 'react-i18next'

/**
 * Component that toggles the theme between light and dark.
 */
export default function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const setLight = useCallback(() => setTheme('light'), [setTheme])
  const setDark = useCallback(() => setTheme('dark'), [setTheme])
  const { t } = useTranslation()

  if (theme === 'dark') {
    return (
      <Button
        onClick={setLight}
        variant={controlButtonVariant}
        tooltip={t('header.themeToggle.switchToLight')}
        size="icon"
        side="bottom"
      >
        <MoonIcon />
      </Button>
    )
  }
  return (
    <Button
      onClick={setDark}
      variant={controlButtonVariant}
      tooltip={t('header.themeToggle.switchToDark')}
      size="icon"
      side="bottom"
    >
      <SunIcon />
    </Button>
  )
}
// @ts-expect-error  MS8yOmFIVnBZMlhtblk3a3ZiUG1yS002VUcxcFp3PT06N2Q1NmQyMmE=
