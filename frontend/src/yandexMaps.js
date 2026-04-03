/** Загрузка JavaScript API Яндекс.Карт 2.1 (один скрипт на страницу). */
let loadPromise = null

export function loadYmaps() {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('Yandex Maps: no window'))
  }

  if (loadPromise) {
    return loadPromise
  }

  loadPromise = new Promise((resolve, reject) => {
    const done = () => {
      window.ymaps.ready(resolve)
    }

    if (window.ymaps) {
      done()
      return
    }

    const id = 'yandex-maps-api-script'
    let script = document.getElementById(id)
    if (script) {
      script.addEventListener('load', done)
      script.addEventListener('error', () => reject(new Error('Yandex Maps: script error')))
      return
    }

    const key = import.meta.env.VITE_YANDEX_MAPS_API_KEY || ''
    script = document.createElement('script')
    script.id = id
    script.async = true
    script.src = `https://api-maps.yandex.ru/2.1/?apikey=${encodeURIComponent(key)}&lang=ru_RU`
    script.onload = done
    script.onerror = () => reject(new Error('Yandex Maps: load failed'))
    document.head.appendChild(script)
  })

  return loadPromise
}
