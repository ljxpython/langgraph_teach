// NOTE  MC8yOmFIVnBZMlhtblk3a3ZiUG1yS002VGpkWFdBPT06ZmI4Yzc4YjI=

import { useState, useEffect } from 'react'
// FIXME  MS8yOmFIVnBZMlhtblk3a3ZiUG1yS002VGpkWFdBPT06ZmI4Yzc4YjI=

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(timer)
    }
  }, [value, delay])

  return debouncedValue
}
