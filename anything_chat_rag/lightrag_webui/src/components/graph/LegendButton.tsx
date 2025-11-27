import { useCallback } from 'react'
import { BookOpenIcon } from 'lucide-react'
import Button from '@/components/ui/Button'
import { controlButtonVariant } from '@/lib/constants'
import { useSettingsStore } from '@/stores/settings'
import { useTranslation } from 'react-i18next'
// NOTE  MC8yOmFIVnBZMlhtblk3a3ZiUG1yS002VmxOcWR3PT06NWEwMGExOTQ=

/**
 * Component that toggles legend visibility.
 */
const LegendButton = () => {
  const { t } = useTranslation()
  const showLegend = useSettingsStore.use.showLegend()
  const setShowLegend = useSettingsStore.use.setShowLegend()

  const toggleLegend = useCallback(() => {
    setShowLegend(!showLegend)
  }, [showLegend, setShowLegend])

  return (
    <Button
      variant={controlButtonVariant}
      onClick={toggleLegend}
      tooltip={t('graphPanel.sideBar.legendControl.toggleLegend')}
      size="icon"
    >
      <BookOpenIcon />
    </Button>
  )
}
// eslint-disable  MS8yOmFIVnBZMlhtblk3a3ZiUG1yS002VmxOcWR3PT06NWEwMGExOTQ=

export default LegendButton
