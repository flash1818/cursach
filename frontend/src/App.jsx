import { useEffect, useMemo, useState } from 'react'
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './App.css'
import {
  demoAnalytics,
  demoCities,
  demoProperties,
  demoPropertyTypes,
} from './data/demoData'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'
const inferBackendOrigin = () => {
  if (typeof window === 'undefined') {
    return 'http://localhost:8000'
  }

  const { protocol, hostname, host, port } = window.location

  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return `${protocol}//${hostname}:8000`
  }

  // GitHub Codespaces: replace frontend marker (-5173) with backend (-8000)
  if (hostname.endsWith('.app.github.dev')) {
    const rewrittenHost = host.replace(/-5173(?=\.|:|$)/, '-8000')
    return `${protocol}//${rewrittenHost}`
  }

  if (port === '5173') {
    return `${protocol}//${hostname}:8000`
  }

  return `${protocol}//${host}`
}

const BACKEND_ORIGIN = import.meta.env.VITE_BACKEND_ORIGIN || inferBackendOrigin()
const DEFAULT_CENTER = [55.7558, 37.6176] // Москва

const initialFilters = {
  search: '',
  city: 'all',
  type: 'all',
  deal: 'all',
  minPrice: '',
  maxPrice: '',
  rooms: 'all',
}

const formatMoney = (value) => {
  const numericValue = Number(value) || 0
  return `${new Intl.NumberFormat('ru-RU').format(Math.round(numericValue))} ₽`
}

const fetchJson = async (url) => {
  try {
    const response = await fetch(url, {
      credentials: 'include',
    })
    if (!response.ok) {
      return null
    }
    return await response.json()
  } catch {
    return null
  }
}

const getPreviewImage = (property) =>
  property?.images?.[0]?.image_url ||
  'https://images.unsplash.com/photo-1560185007-cde436f6a4d0?auto=format&fit=crop&w=900&q=80'

const getTypeLabel = (property, types) => {
  if (property?.property_type_name) return property.property_type_name
  const match = types.find((item) => String(item.id) === String(property?.property_type))
  return match?.name || 'Объект'
}

const getCityLabel = (property, cities) => {
  if (property?.city_name) return property.city_name
  const match = cities.find((item) => String(item.id) === String(property?.city))
  return match?.name || 'Город'
}

const getDistrictLabel = (property) => property?.district_name || 'Без района'

const getNearestMetro = (property) => {
  const links = property?.metro_links
  if (!Array.isArray(links) || !links.length) {
    return null
  }
  const sorted = [...links].sort(
    (a, b) => (a.distance_meters || 0) - (b.distance_meters || 0),
  )
  return sorted[0]
}

function MapFocus({ center, zoom }) {
  const map = useMap()

  useEffect(() => {
    map.setView(center, zoom, { animate: true })
  }, [center, map, zoom])

  return null
}

function StatCard({ label, value, hint }) {
  return (
    <article className="stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{hint}</small>
    </article>
  )
}

function MiniList({ title, items }) {
  const max = Math.max(...items.map((item) => item.count), 1)

  return (
    <div className="mini-list">
      <h3>{title}</h3>
      <div className="mini-list-items">
        {items.map((item) => {
          const label = item.city__name || item.property_type__name || item.status || 'Категория'
          const width = `${Math.max((item.count / max) * 100, 10)}%`

          return (
            <div className="mini-row" key={label}>
              <div className="mini-row-head">
                <span>{label}</span>
                <strong>{item.count}</strong>
              </div>
              <div className="mini-bar">
                <div className="mini-bar-fill" style={{ width }} />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function App() {
  const [remoteProperties, setRemoteProperties] = useState([])
  const [remoteCities, setRemoteCities] = useState([])
  const [remoteTypes, setRemoteTypes] = useState([])
  const [remoteAnalytics, setRemoteAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [notice, setNotice] = useState('')
  const [selectedPropertyId, setSelectedPropertyId] = useState(null)
  const [filters, setFilters] = useState(initialFilters)
  const [currentUser, setCurrentUser] = useState(null)
  const [favorites, setFavorites] = useState([])
  const [favoritePropertyIds, setFavoritePropertyIds] = useState([])
  const [detailsProperty, setDetailsProperty] = useState(null)
  const [activeView, setActiveView] = useState('home')
  const [authPromptOpen, setAuthPromptOpen] = useState(false)

  // если пользователь разлогинился, очищаем избранное
  useEffect(() => {
    if (!currentUser) {
      setFavorites([])
      setFavoritePropertyIds([])
    }
  }, [currentUser])

  const reloadFavorites = async () => {
    if (!currentUser) {
      return
    }
    const favs = await fetchJson(`${API_BASE}/favorites/`)
    if (Array.isArray(favs)) {
      setFavorites(favs)
      setFavoritePropertyIds(favs.map((item) => item.property))
    } else {
      setFavorites([])
      setFavoritePropertyIds([])
    }
  }

  useEffect(() => {
    let isMounted = true

    const loadData = async () => {
      const [properties, cities, types, analytics, me] = await Promise.all([
        fetchJson(`${API_BASE}/properties/`),
        fetchJson(`${API_BASE}/cities/`),
        fetchJson(`${API_BASE}/property-types/`),
        fetchJson(`${API_BASE}/analytics/`),
        fetchJson(`${API_BASE}/auth/me/`),
      ])

      if (!isMounted) {
        return
      }

      const safeProperties = Array.isArray(properties) ? properties : []
      const safeCities = Array.isArray(cities) ? cities : []
      const safeTypes = Array.isArray(types) ? types : []

      setRemoteProperties(safeProperties)
      setRemoteCities(safeCities)
      setRemoteTypes(safeTypes)
      setRemoteAnalytics(analytics)
      setCurrentUser(me && me.id ? me : null)

      if (me && me.id && isMounted) {
        const favs = (await fetchJson(`${API_BASE}/favorites/`)) || []
        if (Array.isArray(favs)) {
          setFavorites(favs)
          setFavoritePropertyIds(favs.map((item) => item.property))
        }
      }

      if (!safeProperties.length) {
        setNotice('Пока нет записей в PostgreSQL, поэтому показаны демо-объекты.')
      }

      setLoading(false)
    }

    loadData()

    return () => {
      isMounted = false
    }
  }, [])

  const properties = remoteProperties.length ? remoteProperties : demoProperties
  const cities = remoteCities.length ? remoteCities : demoCities
  const propertyTypes = remoteTypes.length ? remoteTypes : demoPropertyTypes
  const analytics = remoteAnalytics?.supply?.total_properties
    ? remoteAnalytics
    : demoAnalytics

  const filteredProperties = useMemo(() => {
    return properties.filter((property) => {
      const search = filters.search.trim().toLowerCase()
      const matchesSearch =
        !search ||
        [
          property.title,
          property.address,
          property.city_name,
          property.district_name,
          property.property_type_name,
        ]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(search))

      const matchesCity = filters.city === 'all' || String(property.city) === filters.city
      const matchesType = filters.type === 'all' || String(property.property_type) === filters.type
      const matchesDeal = filters.deal === 'all' || property.deal_type === filters.deal
      const matchesRooms =
        filters.rooms === 'all' ||
        String(property.rooms ?? '') === filters.rooms ||
        (filters.rooms === 'studio' && Number(property.rooms) === 1)

      const minPrice = filters.minPrice ? Number(filters.minPrice) : null
      const maxPrice = filters.maxPrice ? Number(filters.maxPrice) : null
      const propertyPrice = Number(property.price) || 0

      const matchesMinPrice = minPrice === null || propertyPrice >= minPrice
      const matchesMaxPrice = maxPrice === null || propertyPrice <= maxPrice

      return (
        matchesSearch &&
        matchesCity &&
        matchesType &&
        matchesDeal &&
        matchesRooms &&
        matchesMinPrice &&
        matchesMaxPrice
      )
    })
  }, [filters, properties])

  useEffect(() => {
    if (!filteredProperties.length) {
      return
    }

    const exists = filteredProperties.some((item) => item.id === selectedPropertyId)
    if (!exists) {
      setSelectedPropertyId(filteredProperties[0].id)
    }
  }, [filteredProperties, selectedPropertyId])

  useEffect(() => {
    if (properties.length && !selectedPropertyId) {
      setSelectedPropertyId(properties[0].id)
    }
  }, [properties, selectedPropertyId])

  const selectedProperty =
    filteredProperties.find((item) => item.id === selectedPropertyId) ||
    filteredProperties[0] ||
    null

  const mapCenter = useMemo(() => {
    if (!selectedProperty?.latitude || !selectedProperty?.longitude) {
      return DEFAULT_CENTER
    }

    return [Number(selectedProperty.latitude), Number(selectedProperty.longitude)]
  }, [selectedProperty])

  const activeCount = analytics.supply?.active_properties ?? 0
  const totalCount = analytics.supply?.total_properties ?? 0
  const saleCount = analytics.supply?.sale_properties ?? 0
  const rentCount = analytics.supply?.rent_properties ?? 0
  const featuredCount = analytics.supply?.featured_properties ?? 0
  const inquiryCount = analytics.demand?.total_inquiries ?? 0
  const averagePrice = analytics.average?.price ?? 0
  const averageArea = analytics.average?.area ?? 0
  const last30 = analytics.last_30_days || {}
  const avgPrice30 = last30.avg_price_30 || 0
  const avgPriceAll = last30.avg_price_all || 0
  const priceDelta =
    avgPriceAll > 0 ? Math.round(((avgPrice30 - avgPriceAll) / avgPriceAll) * 100) : 0

  const resetFilters = () => {
    setFilters(initialFilters)
  }

  const toggleFavorite = async (propertyId) => {
    if (!currentUser) {
      // не авторизован — показываем окно с предложением войти или зарегистрироваться
      setAuthPromptOpen(true)
      return
    }

    // оптимистично переключаем состояние на фронте
    setFavoritePropertyIds((current) => {
      const exists = current.includes(propertyId)
      return exists ? current.filter((id) => id !== propertyId) : [...current, propertyId]
    })

    try {
      const isFavorite = favoritePropertyIds.includes(propertyId)

      if (isFavorite) {
        const existing = favorites.find((item) => item.property === propertyId)
        if (!existing) {
          // на всякий случай просто перезагрузим список
          await reloadFavorites()
          return
        }

        const response = await fetch(`${API_BASE}/favorites/${existing.id}/`, {
          method: 'DELETE',
          credentials: 'include',
        })
        if (response.ok || response.status === 404) {
          await reloadFavorites()
        }
      } else {
        const response = await fetch(`${API_BASE}/favorites/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({ property: propertyId }),
        })

        if (response.ok) {
          await reloadFavorites()
        }
      }
    } catch {
      // на ошибке просто перезагрузим список при следующем рендере
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-brand">
          <p className="eyebrow">Агентство недвижимости</p>
          <h1>Real Estate Pro</h1>
          <p className="subtitle">
            Современная витрина объектов, аналитика рынка и CRM-контур для работы с клиентами.
          </p>
        </div>

        <nav className="topbar-actions">
          <button
            type="button"
            className={`ghost-link nav-pill-button ${activeView === 'home' ? 'nav-pill-button-active' : ''}`}
            onClick={() => setActiveView('home')}
          >
            Главная
          </button>
          <button
            type="button"
            className={`ghost-link nav-pill-button ${activeView === 'market' ? 'nav-pill-button-active' : ''}`}
            onClick={() => setActiveView('market')}
          >
            Объекты
          </button>
          <button
            type="button"
            className={`ghost-link nav-pill-button ${activeView === 'analytics' ? 'nav-pill-button-active' : ''}`}
            onClick={() => setActiveView('analytics')}
          >
            Аналитика
          </button>
          <span className={`status-pill ${remoteProperties.length ? 'live' : 'demo'}`}>
            {remoteProperties.length ? 'Данные из PostgreSQL' : 'Демо-режим'}
          </span>
          {currentUser ? (
            <a
              className="ghost-link"
              href={`${BACKEND_ORIGIN}/profile/`}
              rel="noreferrer"
            >
              {currentUser.first_name || currentUser.username} · профиль
            </a>
          ) : (
            <a
              className="ghost-link"
              href={`${BACKEND_ORIGIN}/auth/login/`}
              rel="noreferrer"
            >
              Войти в CRM
            </a>
          )}
        </nav>
      </header>

      {notice && activeView !== 'analytics' && <div className="notice">{notice}</div>}

      <main className="page-grid">
        {activeView === 'home' && (
        <section className="panel hero-panel">
          <div className="section-head">
            <div>
              <p className="section-label">О компании</p>
              <h2>Real Estate Pro — цифровое агентство</h2>
            </div>
          </div>

          <div className="hero-intro-grid">
            <div className="hero-copy">
              <p>
                Мы соединяем владельцев недвижимости и покупателей через прозрачную витрину объектов,
                умные фильтры и живую аналитику рынка. Система построена на Django, React и PostgreSQL —
                надёжный стек для реальных сделок.
              </p>
              <p>
                На этой странице вы можете посмотреть актуальные объекты, их расположение на карте и
                динамику рынка по городам и типам недвижимости.
              </p>
            </div>
            <div className="hero-gallery">
              <img
                src="https://images.unsplash.com/photo-1505843513577-22bb7d21e455?auto=format&fit=crop&w=900&q=80"
                alt="Современный жилой комплекс"
              />
              <img
                src="https://images.unsplash.com/photo-1529424301806-4be0bb154e3b?auto=format&fit=crop&w=900&q=80"
                alt="Офисный центр"
              />
            </div>
          </div>

          <div className="divider" />

          <div className="stats-grid">
            <StatCard label="Объекты" value={totalCount} hint="Всего в системе" />
            <StatCard label="Активные" value={activeCount} hint="Доступны сейчас" />
            <StatCard label="Продажа" value={saleCount} hint="Объявления на продажу" />
            <StatCard label="Аренда" value={rentCount} hint="Объявления в аренду" />
            <StatCard label="Избранные" value={featuredCount} hint="Продвигаемые объекты" />
            <StatCard label="Заявки" value={inquiryCount} hint="Лиды и обращения" />
          </div>

          <div className="hero-metrics">
            <div className="metric-chip">
              <span>Средняя цена</span>
              <strong>{formatMoney(averagePrice)}</strong>
            </div>
            <div className="metric-chip">
              <span>Средняя площадь</span>
              <strong>{averageArea} м²</strong>
            </div>
            <div className="metric-chip">
              <span>Подключение</span>
              <strong>{loading ? 'Загрузка...' : 'Готово'}</strong>
            </div>
          </div>
        </section>
        )}

        {activeView === 'market' && (
        <section className="content-grid">
          <aside className="panel filters-panel">
            <div className="section-head compact">
              <div>
                <p className="section-label">Поиск</p>
                <h2>Фильтры</h2>
              </div>
            </div>

            <div className="filters-header-row">
              <div className="filters-pill-row">
                <button
                  type="button"
                  className={`filter-pill ${filters.deal === 'all' ? 'filter-pill-active' : ''}`}
                  onClick={() => setFilters((current) => ({ ...current, deal: 'all' }))}
                >
                  Все сделки
                </button>
                <button
                  type="button"
                  className={`filter-pill ${filters.deal === 'sale' ? 'filter-pill-active' : ''}`}
                  onClick={() => setFilters((current) => ({ ...current, deal: 'sale' }))}
                >
                  Продажа
                </button>
                <button
                  type="button"
                  className={`filter-pill ${filters.deal === 'rent' ? 'filter-pill-active' : ''}`}
                  onClick={() => setFilters((current) => ({ ...current, deal: 'rent' }))}
                >
                  Аренда
                </button>
              </div>
              <button type="button" className="link-button" onClick={resetFilters}>
                Сбросить
              </button>
            </div>

            <label className="field">
              <span>Поиск</span>
              <input
                type="text"
                value={filters.search}
                onChange={(event) =>
                  setFilters((current) => ({ ...current, search: event.target.value }))
                }
                placeholder="Квартира, район, адрес..."
              />
            </label>

            <label className="field">
              <span>Город</span>
              <select
                value={filters.city}
                onChange={(event) =>
                  setFilters((current) => ({ ...current, city: event.target.value }))
                }
              >
                <option value="all">Все города</option>
                {cities.map((city) => (
                  <option key={city.id} value={city.id}>
                    {city.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Тип объекта</span>
              <select
                value={filters.type}
                onChange={(event) =>
                  setFilters((current) => ({ ...current, type: event.target.value }))
                }
              >
                <option value="all">Все типы</option>
                {propertyTypes.map((type) => (
                  <option key={type.id} value={type.id}>
                    {type.name}
                  </option>
                ))}
              </select>
            </label>

            <div className="double-field">
              <label className="field">
                <span>Цена от</span>
                <input
                  type="number"
                  min="0"
                  value={filters.minPrice}
                  onChange={(event) =>
                    setFilters((current) => ({ ...current, minPrice: event.target.value }))
                  }
                  placeholder="0"
                />
              </label>

              <label className="field">
                <span>Цена до</span>
                <input
                  type="number"
                  min="0"
                  value={filters.maxPrice}
                  onChange={(event) =>
                    setFilters((current) => ({ ...current, maxPrice: event.target.value }))
                  }
                  placeholder="100000000"
                />
              </label>
            </div>

            <label className="field">
              <span>Комнаты</span>
              <select
                value={filters.rooms}
                onChange={(event) =>
                  setFilters((current) => ({ ...current, rooms: event.target.value }))
                }
              >
                <option value="all">Любое количество</option>
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4</option>
                <option value="5">5+</option>
              </select>
            </label>
          </aside>

          <section className="panel catalog-panel">
            <div className="section-head compact">
              <div>
                <p className="section-label">Каталог</p>
                <h2>Объекты недвижимости</h2>
              </div>
              <span className="result-count">
                {filteredProperties.length} из {properties.length}
              </span>
            </div>

            <div className="cards-grid">
              {loading ? (
                <div className="empty-state">Загружаем данные из API...</div>
              ) : filteredProperties.length ? (
                filteredProperties.map((property) => {
                  const isSelected = selectedProperty?.id === property.id
                  const isFavorite = favoritePropertyIds.includes(property.id)

                  return (
                    <article
                      key={property.id}
                      className={`property-card ${isSelected ? 'selected' : ''}`}
                      onClick={() => {
                        setSelectedPropertyId(property.id)
                        setDetailsProperty(property)
                      }}
                    >
                      <img
                        className="property-image"
                        src={getPreviewImage(property)}
                        alt={property.title}
                      />
                      <div className="property-body">
                        <div className="property-topline">
                          <span className={`badge ${property.deal_type}`}>
                            {property.deal_type === 'sale' ? 'Продажа' : 'Аренда'}
                          </span>
                          {property.is_featured && <span className="badge featured">Выбор</span>}
                        </div>

                        <h3>{property.title}</h3>
                        <p className="property-address">
                          {getCityLabel(property, cities)}, {getDistrictLabel(property)}
                        </p>
                        <p className="property-description">{property.description}</p>

                        <div className="property-meta">
                          <span>{getTypeLabel(property, propertyTypes)}</span>
                          <span>{property.area} м²</span>
                          <span>{property.rooms ?? '—'} комн.</span>
                        </div>

                        <div className="property-footer">
                          <strong>{formatMoney(property.price)}</strong>
                          <span>{property.floor ? `${property.floor} этаж` : '1 этаж'}</span>
                          <button
                            type="button"
                            className={`favorite-button ${isFavorite ? 'favorite-button--active' : ''}`}
                            onClick={(event) => {
                              event.stopPropagation()
                              toggleFavorite(property.id)
                            }}
                          >
                            {isFavorite ? 'В избранном' : 'В избранное'}
                          </button>
                        </div>
                      </div>
                    </article>
                  )
                })
              ) : (
                <div className="empty-state">
                  Ничего не найдено по выбранным фильтрам.
                </div>
              )}
            </div>
          </section>
        </section>
        )}

        {activeView === 'market' && (
        <section className="map-panel panel">
          <div className="section-head compact">
            <div>
              <p className="section-label">Карта</p>
              <h2>Интеграция с Leaflet</h2>
            </div>
            <span className="result-count">
              {selectedProperty ? selectedProperty.title : 'Нет объекта'}
            </span>
          </div>

          <div className="map-box">
            <MapContainer
              center={mapCenter}
              zoom={12}
              scrollWheelZoom
              className="leaflet-map"
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <MapFocus center={mapCenter} zoom={12} />
              {filteredProperties.map((property) => {
                if (!property.latitude || !property.longitude) {
                  return null
                }

                const isSelected = selectedProperty?.id === property.id
                const lat = Number(property.latitude)
                const lng = Number(property.longitude)

                return (
                  <CircleMarker
                    key={property.id}
                    center={[lat, lng]}
                    radius={isSelected ? 11 : 8}
                    pathOptions={{
                      color: isSelected ? '#f59e0b' : '#3b82f6',
                      fillColor: isSelected ? '#fbbf24' : '#60a5fa',
                      fillOpacity: 0.85,
                      weight: 2,
                    }}
                    eventHandlers={{
                      click: () => setSelectedPropertyId(property.id),
                    }}
                  >
                    <Popup>
                      <div className="popup-card">
                        <strong>{property.title}</strong>
                        <span>{getCityLabel(property, cities)}</span>
                        <span>{formatMoney(property.price)}</span>
                      </div>
                    </Popup>
                  </CircleMarker>
                )
              })}
            </MapContainer>
          </div>
        </section>
        )}

        {activeView === 'analytics' && (
        <section className="analytics-panel panel">
          <div className="section-head compact">
            <div>
              <p className="section-label">Аналитика</p>
              <h2>Спрос и предложение</h2>
            </div>
          </div>

          <div className="analytics-grid">
            <div className="analytics-card">
              <span>Предложение</span>
              <strong>{analytics.supply?.total_properties ?? 0}</strong>
              <p>Всего объектов в базе</p>
            </div>
            <div className="analytics-card">
              <span>Спрос</span>
              <strong>{analytics.demand?.total_inquiries ?? 0}</strong>
              <p>Обращения от клиентов</p>
            </div>
            <div className="analytics-card">
              <span>Средняя цена</span>
              <strong>{formatMoney(averagePrice)}</strong>
              <p>По всем объектам</p>
            </div>
            <div className="analytics-card">
              <span>Средняя площадь</span>
              <strong>{averageArea} м²</strong>
              <p>По всем объектам</p>
            </div>
          </div>

          <div className="analytics-grid">
            <div className="analytics-card">
              <span>Новые объекты за 30 дней</span>
              <strong>{last30.new_properties ?? 0}</strong>
              <p>Сколько объектов добавлено за последний месяц</p>
            </div>
            <div className="analytics-card">
              <span>Новые заявки за 30 дней</span>
              <strong>{last30.new_inquiries ?? 0}</strong>
              <p>Активность клиентов за последний месяц</p>
            </div>
            <div className="analytics-card">
              <span>Средняя цена (30 дней)</span>
              <strong>{formatMoney(avgPrice30)}</strong>
              <p>По объектам, добавленным за 30 дней</p>
            </div>
            <div className="analytics-card">
              <span>Изменение средней цены</span>
              <strong>
                {priceDelta > 0 && '+'}
                {priceDelta}%
              </strong>
              <p>К общей средней цене по базе</p>
            </div>
          </div>

          <div className="analytics-lists">
            <MiniList title="По городам" items={analytics.by_city ?? []} />
            <MiniList title="По типам" items={analytics.by_property_type ?? []} />
            <MiniList title="Заявки по городам" items={analytics.inquiries_by_city ?? []} />
          </div>
        </section>
        )}
      </main>

      {detailsProperty && (
        <div
          className="details-modal-backdrop"
          onClick={() => setDetailsProperty(null)}
        >
          <div
            className="details-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="details-modal-header">
              <div>
                <p className="section-label">Объект</p>
                <h2>{detailsProperty.title}</h2>
                <p className="property-address">
                  {getCityLabel(detailsProperty, cities)}, {getDistrictLabel(detailsProperty)}
                </p>
                <p className="details-address">Адрес: {detailsProperty.address}</p>
              </div>
              <button
                type="button"
                className="ghost-link"
                onClick={() => setDetailsProperty(null)}
              >
                Закрыть
              </button>
            </div>

            <div className="details-modal-grid">
              <div className="details-main">
                <p className="details-description">{detailsProperty.description}</p>

                <div className="details-metro">
                  <span>Ближайшее метро:</span>
                  {getNearestMetro(detailsProperty) ? (
                    <>
                      <strong>{getNearestMetro(detailsProperty).station_name}</strong>
                      <span>
                        {getNearestMetro(detailsProperty).distance_meters} м ·{' '}
                        {getNearestMetro(detailsProperty).walking_time_minutes} мин пешком
                      </span>
                    </>
                  ) : (
                    <span>Отсутствует</span>
                  )}
                </div>

                <div className="details-specs">
                  <span>{getTypeLabel(detailsProperty, propertyTypes)}</span>
                  <span>Площадь: {detailsProperty.area} м²</span>
                  <span>Комнаты: {detailsProperty.rooms ?? '—'}</span>
                  <span>
                    Этаж: {detailsProperty.floor ?? '—'}
                    {detailsProperty.total_floors && ` из ${detailsProperty.total_floors}`}
                  </span>
                  <span>Статус: {detailsProperty.status}</span>
                </div>

                <div className="details-price">
                  <strong>{formatMoney(detailsProperty.price)}</strong>
                  <span>
                    Тип сделки: {detailsProperty.deal_type === 'sale' ? 'Продажа' : 'Аренда'}
                  </span>
                  <button
                    type="button"
                    className={`favorite-button ${
                      favoritePropertyIds.includes(detailsProperty.id) ? 'favorite-button--active' : ''
                    }`}
                    onClick={() => toggleFavorite(detailsProperty.id)}
                  >
                    {favoritePropertyIds.includes(detailsProperty.id) ? 'В избранном' : 'В избранное'}
                  </button>
                </div>
              </div>

              <aside className="details-side">
                <h3>Местоположение на карте</h3>
                <div className="details-map-box">
                  <MapContainer
                    center={
                      detailsProperty.latitude && detailsProperty.longitude
                        ? [Number(detailsProperty.latitude), Number(detailsProperty.longitude)]
                        : mapCenter
                    }
                    zoom={13}
                    scrollWheelZoom
                    className="leaflet-map"
                  >
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    {detailsProperty.latitude && detailsProperty.longitude && (
                      <CircleMarker
                        center={[
                          Number(detailsProperty.latitude),
                          Number(detailsProperty.longitude),
                        ]}
                        radius={10}
                        pathOptions={{
                          color: '#f59e0b',
                          fillColor: '#fbbf24',
                          fillOpacity: 0.9,
                          weight: 2,
                        }}
                      >
                        <Popup>
                          <div className="popup-card">
                            <strong>{detailsProperty.title}</strong>
                            <span>{getCityLabel(detailsProperty, cities)}</span>
                            <span>{formatMoney(detailsProperty.price)}</span>
                          </div>
                        </Popup>
                      </CircleMarker>
                    )}
                  </MapContainer>
                </div>
              </aside>
            </div>
          </div>
        </div>
      )}
      {authPromptOpen && (
        <div
          className="details-modal-backdrop"
          onClick={() => setAuthPromptOpen(false)}
        >
          <div
            className="details-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="details-modal-header">
              <div>
                <p className="section-label">Только для авторизованных</p>
                <h2>Войдите, чтобы добавить в избранное</h2>
                <p className="subtitle">
                  Сохранённые объекты будут доступны в вашем личном кабинете.
                </p>
              </div>
              <button
                type="button"
                className="ghost-link"
                onClick={() => setAuthPromptOpen(false)}
              >
                Закрыть
              </button>
            </div>
            <div className="auth-prompt-actions">
              <a
                href={`${BACKEND_ORIGIN}/auth/login/`}
                className="primary-link-button"
              >
                Войти
              </a>
              <a
                href={`${BACKEND_ORIGIN}/auth/register/`}
                className="ghost-link-button"
              >
                Зарегистрироваться
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App

