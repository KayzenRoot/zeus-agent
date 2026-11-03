import { OnboardingEnd } from '@/components/onboarding/onboarding-end'
import { isAuxiliaryWindow } from '@/store/windows'

import { EntitlementActivationOverlay } from './activation-overlay'

interface Props {
  enabled: boolean
}

/** Post-onboarding blockers shared by every primary window. */
export function PostOnboardingSurfaces({ enabled }: Props) {
  if (isAuxiliaryWindow()) {
    return null
  }

  return (
    <>
      <OnboardingEnd />
      <EntitlementActivationOverlay enabled={enabled} />
    </>
  )
}
