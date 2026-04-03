import { useEffect, useRef, useState } from 'react'
import { loadYmaps } from './yandexMaps'

/**
 * Карта Яндекса: центр [широта, долгота], метки с балуном (HTML).
 * @param {object} props
 * @param {string} [props.className]
 * @param {[number, number]} props.center
 * @param {number} props.zoom
 * @param {Array<{ id: string|number, lat: number, lng: number, selected?: boolean, balloonHtml?: string }>} [props.markers]
 * @param {(id: string|number) => void} [props.onMarkerClick]
 */
export default function YandexMap({
  className,
  center,
  zoom,
  markers = [],
  onMarkerClick,
}) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const collectionRef = useRef(null)
  const [mapReady, setMapReady] = useState(false)
  const onMarkerClickRef = useRef(onMarkerClick)
  const centerRef = useRef(center)
  const zoomRef = useRef(zoom)

  centerRef.current = center
  zoomRef.current = zoom

  useEffect(() => {
    onMarkerClickRef.current = onMarkerClick
  }, [onMarkerClick])

  useEffect(() => {
    let cancelled = false
    let mapInstance = null

    loadYmaps()
      .then(() => {
        if (cancelled || !containerRef.current) {
          return
        }
        const ymaps = window.ymaps
        mapInstance = new ymaps.Map(containerRef.current, {
          center: centerRef.current,
          zoom: zoomRef.current,
          controls: ['zoomControl', 'fullscreenControl'],
        })
        const collection = new ymaps.GeoObjectCollection()
        mapInstance.geoObjects.add(collection)
        mapRef.current = mapInstance
        collectionRef.current = collection
        setMapReady(true)
      })
      .catch(() => {
        setMapReady(false)
      })

    return () => {
      cancelled = true
      setMapReady(false)
      mapRef.current = null
      collectionRef.current = null
      if (mapInstance) {
        mapInstance.destroy()
      }
    }
  }, [])

  useEffect(() => {
    if (!mapReady || !mapRef.current) {
      return
    }
    mapRef.current.setCenter(center, zoom, { duration: 200 })
  }, [mapReady, center, zoom])

  useEffect(() => {
    if (!mapReady || !collectionRef.current) {
      return
    }
    const ymaps = window.ymaps
    const collection = collectionRef.current
    collection.removeAll()

    markers.forEach((m) => {
      const placemark = new ymaps.Placemark(
        [m.lat, m.lng],
        m.balloonHtml
          ? { balloonContentBody: m.balloonHtml, balloonContentMaxWidth: 280 }
          : {},
        {
          preset: m.selected
            ? 'islands#orangeCircleDotIcon'
            : 'islands#blueCircleDotIcon',
        },
      )
      placemark.events.add('click', () => {
        onMarkerClickRef.current?.(m.id)
      })
      collection.add(placemark)
    })
  }, [mapReady, markers])

  return <div ref={containerRef} className={className} />
}
