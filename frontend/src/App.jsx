import { useEffect, useMemo, useRef, useState } from 'react'
import './App.css'
import YandexMap from './YandexMap'
import {
  demoAnalytics,
  demoCities,
  demoProperties,
  demoPropertyTypes,
} from './data/demoData'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'
const BACKEND_ORIGIN = import.meta.env.VITE_BACKEND_ORIGIN || ''

function readCookie(name) {
  const safe = name.replace(/[$()*+.?[\\\]^{|}]/g, '\\$&')
  const m = document.cookie.match(new RegExp(`(?:^|; )${safe}=([^;]*)`))
  return m ? decodeURIComponent(m[1]) : ''
}

function csrfHeaderObj(json = false) {
  const token = readCookie('csrftoken')
  const headers = { 'X-CSRFToken': token || '' }
  if (json) {
    headers['Content-Type'] = 'application/json'
  }
  return headers
}
/**
 * Ссылки на Django (вход, профиль). На Vite :5173 всегда относительные пути,
 * иначе сессия с localhost:8000 не попадает в fetch('/api/...') с :5173 — «К сделке» и API без авторизации.
 */
const backendHref = (path) => {
  if (typeof window !== 'undefined' && window.location.port === '5173') {
    return path
  }
  return BACKEND_ORIGIN ? `${BACKEND_ORIGIN}${path}` : path
}
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

const escapeHtml = (value) =>
  String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')

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

const PLACEHOLDER_IMG =
  'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800"><rect width="1200" height="800" fill="%231e293b"/><text x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%23cbd5e1" font-size="42" font-family="Arial,sans-serif">Фото недоступно</text></svg>'

const getPreviewImage = (property) => property?.images?.[0]?.image_url || PLACEHOLDER_IMG

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

function StatCard({ label, value, hint }) {
  return (
    <article className="stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{hint}</small>
    </article>
  )
}

const WHY_US_MARQUEE = [
  'Юридическая проверка каждого объекта',
  'Сопровождение сделки «под ключ»',
  'Помощь с ипотекой и одобрением',
  'Прозрачный договор и комиссия',
  'Личный риэлтор на весь цикл',
  'База объектов без «мёртвых» объявлений',
  'Быстрый ответ в мессенджере и по телефону',
  'Оценка рыночной стоимости',
  'Переговоры с продавцом и торг',
  'Проверка застройщика и ДДУ',
  'Сдача и приёмка квартиры',
  'Регистрация права в Росреестре',
  'Коммерческая и жилая недвижимость',
  'Аренда с подбором надёжных арендаторов',
  'Релокация и переезд «под ключ»',
  'Страхование и безопасные расчёты',
  'Фото, 3D-туры и честные описания',
  'Аналитика по районам и ценам',
  'Послепродажная поддержка',
  'Конфиденциальность данных клиента',
]

const WHY_US_SLIDES = [
  {
    title: 'Опыт и команда',
    body:
      'В агентстве работают сертифицированные риэлторы, юристы и аналитики рынка. Мы знаем локальные особенности Москвы, Санкт-Петербурга и регионов: от типовых договоров до спорных ситуаций с обременениями и долевым участием.',
  },
  {
    title: 'Безопасность сделки',
    body:
      'Проверяем документы, историю объекта, зарегистрированные обременения и полномочия продавца. Подсказываем безопасные схемы расчётов и сопровождаем регистрацию перехода права, чтобы вы не столкнулись с сюрпризами после подписания.',
  },
  {
    title: 'Ипотека и финансы',
    body:
      'Помогаем собрать пакет документов, сравнить программы банков и пройти одобрение. Объясняем ставки, страховки и ежемесячный платёж простым языком — вы принимаете решение осознанно, без навязанных продуктов.',
  },
  {
    title: 'Экономия времени',
    body:
      'Отбираем только релевантные варианты под ваш бюджет, район и сценарий жизни. Организуем просмотры, переговоры и повторные выезды так, чтобы не тратить ваши вечера и выходные на бессмысленные показы.',
  },
  {
    title: 'Честный маркетинг',
    body:
      'В карточках объектов — актуальные фото, реальные площади и статусы. Не приукрашиваем «под звонок»: если объект не подходит, скажем прямо и предложим альтернативы, чтобы вы быстрее пришли к результату.',
  },
  {
    title: 'Коммерция и инвестиции',
    body:
      'Работаем с офисами, торговыми площадями и помещениями под бизнес. Оцениваем окупаемость, проходимость и юридические ограничения по назначению помещения — важно как для старта, так и для портфеля.',
  },
  {
    title: 'Аренда без стресса',
    body:
      'Подбираем жильё или площадь под задачу, согласовываем условия договора, депозит и сроки. Помогаем с приёмкой-передачей и фиксацией состояния объекта, чтобы аренда не превратилась в спорные «а это было / не было».',
  },
  {
    title: 'Сервис после сделки',
    body:
      'Остаёмся на связи: подскажем по ЖКУ, переоформлению, налоговым вычетам и типовым вопросам новосёлов. Наша цель — не разовая продажа, а рекомендации друзьям и возвращение клиентов за следующей сделкой.',
  },
  {
    title: 'Технологии и прозрачность',
    body:
      'Каталог, карта и аналитика доступны онлайн: вы в любой момент видите статусы объектов и рыночный контекст. Документы и договорённости фиксируем письменно — никаких «устных обещаний», которые потом невозможно проверить.',
  },
  {
    title: 'Почему именно мы',
    body:
      'Мы совмещаем человеческий подход и дисциплину процессов: понятные этапы, предсказуемые сроки и ответственность за результат. Если готовы обсудить задачу — начните с раздела «Объекты» или оставьте заявку через профиль после входа на сайт.',
  },
]

function WhyUsSection() {
  const [slide, setSlide] = useState(0)
  const n = WHY_US_SLIDES.length

  useEffect(() => {
    if (
      typeof window !== 'undefined' &&
      window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    ) {
      return undefined
    }
    const t = window.setInterval(() => {
      setSlide((s) => (s + 1) % n)
    }, 5200)
    return () => window.clearInterval(t)
  }, [n])

  const doubledMarquee = [...WHY_US_MARQUEE, ...WHY_US_MARQUEE]

  return (
    <div className="why-us-block">
      <div className="why-us-head">
        <p className="section-label">Преимущества</p>
        <h3 className="why-us-title">Почему клиенты выбирают Real Estate Pro</h3>
        <p className="why-us-lead">
          Полный цикл работы с недвижимостью: от подбора и проверки до ключей в руках и поддержки после
          сделки. Ниже — кратко о том, что вы получаете, работая с нашей командой.
        </p>
      </div>

      <div className="why-marquee" aria-label="Ключевые преимущества агентства">
        <div className="why-marquee-track">
          {doubledMarquee.map((text, i) => (
            <span className="why-marquee-pill" key={`${text}-${i}`}>
              {text}
            </span>
          ))}
        </div>
      </div>

      <div className="why-marquee why-marquee--reverse" aria-hidden="true">
        <div className="why-marquee-track why-marquee-track--slow">
          {[...WHY_US_MARQUEE].reverse().concat([...WHY_US_MARQUEE].reverse()).map((text, i) => (
            <span className="why-marquee-pill why-marquee-pill--alt" key={`r-${text}-${i}`}>
              {text}
            </span>
          ))}
        </div>
      </div>

      <div className="why-carousel" role="region" aria-roledescription="carousel" aria-label="Подробно о компании">
        <div className="why-carousel-viewport">
          {WHY_US_SLIDES.map((item, i) => (
            <article
              key={item.title}
              className={`why-carousel-slide${i === slide ? ' why-carousel-slide--active' : ''}`}
              aria-hidden={i !== slide}
            >
              <h4 className="why-carousel-slide-title">{item.title}</h4>
              <p className="why-carousel-slide-body">{item.body}</p>
            </article>
          ))}
        </div>
        <div className="why-carousel-footer">
          <div className="why-carousel-progress" key={slide}>
            <div className="why-carousel-progress-bar" />
          </div>
          <div className="why-carousel-dots" role="tablist" aria-label="Слайды">
            {WHY_US_SLIDES.map((item, i) => (
              <button
                key={item.title}
                type="button"
                role="tab"
                aria-selected={i === slide}
                className={`why-carousel-dot${i === slide ? ' why-carousel-dot--active' : ''}`}
                onClick={() => setSlide(i)}
                aria-label={`Слайд ${i + 1}: ${item.title}`}
              />
            ))}
          </div>
        </div>
      </div>

      <ul className="why-us-grid">
        <li>
          <strong>15+ лет суммарного опыта команды</strong>
          <span>Сложные сделки, новостройки и вторичка — в одном окне.</span>
        </li>
        <li>
          <strong>Единая точка контакта</strong>
          <span>Один ответственный риэлтор ведёт историю переговоров и документов.</span>
        </li>
        <li>
          <strong>Договор и цифры до старта</strong>
          <span>Фиксируем условия сотрудничества до показов и брони.</span>
        </li>
        <li>
          <strong>Гибкий график</strong>
          <span>Встречи и просмотры в удобное время, в том числе онлайн.</span>
        </li>
        <li>
          <strong>Партнёры по сервису</strong>
          <span>Оценщики, нотариусы, переезды — по запросу, без навязывания.</span>
        </li>
        <li>
          <strong>Репутация</strong>
          <span>Работаем на рекомендации: большинство клиентов приходят по отзывам.</span>
        </li>
      </ul>
    </div>
  )
}

function MiniList({ title, items }) {
  const max = Math.max(...items.map((item) => item.count), 1)

  return (
    <div className="mini-list">
      <h3>{title}</h3>
      <div className="mini-list-items">
        {items.map((item, index) => {
          const label = item.city__name || item.property_type__name || item.status || 'Категория'
          const width = `${Math.max((item.count / max) * 100, 10)}%`

          return (
            <div className="mini-row" key={`${label}-${index}`}>
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
  const [detailSessionKey, setDetailSessionKey] = useState(0)
  const [activeView, setActiveView] = useState('home')
  const [authPromptOpen, setAuthPromptOpen] = useState(false)
  const [authPromptKind, setAuthPromptKind] = useState('favorite')
  const [dealSubmitting, setDealSubmitting] = useState(false)
  const [detailsPhotoIndex, setDetailsPhotoIndex] = useState(0)
  const detailsSwipeRef = useRef({ x: 0 })
  const [companyGallery, setCompanyGallery] = useState([])
  const [similarProperties, setSimilarProperties] = useState([])
  const [priceChatOpen, setPriceChatOpen] = useState(false)
  const [priceChatMessages, setPriceChatMessages] = useState([])
  const [priceChatInput, setPriceChatInput] = useState('')
  const priceChatWsRef = useRef(null)

  // если пользователь разлогинился, очищаем избранное
  useEffect(() => {
    if (!currentUser) {
      setFavorites([])
      setFavoritePropertyIds([])
    }
  }, [currentUser])

  useEffect(() => {
    setDetailsPhotoIndex(0)
  }, [detailsProperty?.id])

  useEffect(() => {
    if (!detailsProperty) {
      setPriceChatOpen(false)
      setPriceChatMessages([])
      setPriceChatInput('')
    }
  }, [detailsProperty])

  useEffect(() => {
    if (!detailsProperty?.id) {
      setSimilarProperties([])
      return
    }
    if (!remoteProperties.length) {
      setSimilarProperties([])
      return
    }
    let cancelled = false
    ;(async () => {
      await fetch(`${API_BASE}/auth/csrf/`, { credentials: 'include' })
      const full = await fetchJson(`${API_BASE}/properties/${detailsProperty.id}/`)
      if (!cancelled && full?.id) {
        setDetailsProperty((prev) => (prev && prev.id === full.id ? { ...prev, ...full } : prev))
      }
      const sim = await fetchJson(`${API_BASE}/similar/${detailsProperty.id}/`)
      if (!cancelled && Array.isArray(sim)) {
        setSimilarProperties(sim)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [detailsProperty?.id, remoteProperties.length, detailSessionKey])

  useEffect(() => {
    if (!priceChatOpen || !detailsProperty?.id || !currentUser || !remoteProperties.length) {
      return undefined
    }
    let cancelled = false
    ;(async () => {
      await fetch(`${API_BASE}/auth/csrf/`, { credentials: 'include' })
      const r = await fetch(`${API_BASE}/properties/${detailsProperty.id}/chat/`, {
        credentials: 'include',
      })
      if (!r.ok || cancelled) {
        return
      }
      const data = await r.json()
      if (!Array.isArray(data) || cancelled) {
        return
      }
      setPriceChatMessages(
        data.map((m) => ({
          id: m.id,
          user: m.sender_username,
          text: m.body,
          created_at: m.created_at,
        })),
      )
    })()
    return () => {
      cancelled = true
    }
  }, [priceChatOpen, detailsProperty?.id, currentUser, remoteProperties.length])

  useEffect(() => {
    if (!priceChatOpen || !detailsProperty?.id || !currentUser) {
      if (priceChatWsRef.current) {
        try {
          priceChatWsRef.current.close()
        } catch {
          /* ignore */
        }
        priceChatWsRef.current = null
      }
      return undefined
    }
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(
      `${proto}//${window.location.host}/ws/chat/${detailsProperty.id}/`,
    )
    priceChatWsRef.current = ws
    ws.onmessage = (ev) => {
      try {
        const d = JSON.parse(ev.data)
        setPriceChatMessages((prev) => {
          const mid = d.id
          if (mid != null && prev.some((x) => x.id === mid)) {
            return prev
          }
          return [
            ...prev,
            {
              id: d.id,
              user: d.username,
              text: d.message,
              created_at: d.created_at,
            },
          ]
        })
      } catch {
        /* ignore */
      }
    }
    return () => {
      try {
        ws.close()
      } catch {
        /* ignore */
      }
      priceChatWsRef.current = null
    }
  }, [priceChatOpen, detailsProperty?.id, currentUser])

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
      await fetch(`${API_BASE}/auth/csrf/`, { credentials: 'include' })
      const [properties, cities, types, analytics, me, gallery] = await Promise.all([
        fetchJson(`${API_BASE}/properties/`),
        fetchJson(`${API_BASE}/cities/`),
        fetchJson(`${API_BASE}/property-types/`),
        fetchJson(`${API_BASE}/analytics/`),
        fetchJson(`${API_BASE}/auth/me/`),
        fetchJson(`${API_BASE}/company-gallery/`),
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
      setCompanyGallery(Array.isArray(gallery) ? gallery : [])

      if (me && me.id && isMounted) {
        const favs = (await fetchJson(`${API_BASE}/favorites/`)) || []
        if (Array.isArray(favs)) {
          setFavorites(favs)
          setFavoritePropertyIds(favs.map((item) => item.property))
        }
      }

      if (!safeProperties.length) {
        setNotice('Пока нет объектов в каталоге — показаны демонстрационные примеры.')
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

  const catalogMapMarkers = useMemo(
    () =>
      filteredProperties
        .filter((property) => property.latitude && property.longitude)
        .map((property) => ({
          id: property.id,
          lat: Number(property.latitude),
          lng: Number(property.longitude),
          selected: selectedProperty?.id === property.id,
          balloonHtml: `<div class="popup-card"><strong>${escapeHtml(property.title)}</strong><span>${escapeHtml(getCityLabel(property, cities))}</span><span>${escapeHtml(formatMoney(property.price))}</span></div>`,
        })),
    [filteredProperties, selectedProperty, cities],
  )

  const detailsMapMarkers = useMemo(() => {
    if (!detailsProperty?.latitude || !detailsProperty?.longitude) {
      return []
    }
    return [
      {
        id: detailsProperty.id,
        lat: Number(detailsProperty.latitude),
        lng: Number(detailsProperty.longitude),
        selected: true,
        balloonHtml: `<div class="popup-card"><strong>${escapeHtml(detailsProperty.title)}</strong><span>${escapeHtml(getCityLabel(detailsProperty, cities))}</span><span>${escapeHtml(formatMoney(detailsProperty.price))}</span></div>`,
      },
    ]
  }, [detailsProperty, cities])

  const detailsMapCenter = useMemo(() => {
    if (detailsProperty?.latitude && detailsProperty?.longitude) {
      return [Number(detailsProperty.latitude), Number(detailsProperty.longitude)]
    }
    return mapCenter
  }, [detailsProperty, mapCenter])

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
  const pricePerSqm =
    averagePrice > 0 && averageArea > 0 ? Math.round(averagePrice / averageArea) : 0
  const inquiriesPerListing =
    totalCount > 0 ? (inquiryCount / totalCount).toFixed(1) : null
  const saleSharePct = totalCount > 0 ? Math.round((saleCount / totalCount) * 100) : 0
  const rentSharePct = totalCount > 0 ? Math.max(0, 100 - saleSharePct) : 0
  const activeSharePct = totalCount > 0 ? Math.round((activeCount / totalCount) * 100) : 0
  const newInq = analytics.demand?.new_inquiries ?? 0
  const inProgressInq = analytics.demand?.in_progress_inquiries ?? 0

  const resetFilters = () => {
    setFilters(initialFilters)
  }

  const closeAuthPrompt = () => {
    setAuthPromptOpen(false)
    setAuthPromptKind('favorite')
  }

  const toggleFavorite = async (propertyId) => {
    if (!currentUser) {
      setAuthPromptKind('favorite')
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
          headers: csrfHeaderObj(false),
        })
        if (response.ok || response.status === 404) {
          await reloadFavorites()
        }
      } else {
        const response = await fetch(`${API_BASE}/favorites/`, {
          method: 'POST',
          headers: csrfHeaderObj(true),
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

  const handleDealInterest = async () => {
    if (!detailsProperty) {
      return
    }
    if (!currentUser) {
      setAuthPromptKind('deal')
      setAuthPromptOpen(true)
      return
    }
    if (currentUser.role === 'realtor') {
      setNotice(
        'Кнопка «К сделке» доступна клиентам. Зарегистрируйте отдельный аккаунт клиента или войдите под ним.',
      )
      return
    }

    setDealSubmitting(true)
    try {
      const response = await fetch(
        `${API_BASE}/properties/${detailsProperty.id}/deal-interest/`,
        {
          method: 'POST',
          credentials: 'include',
          headers: csrfHeaderObj(true),
          body: JSON.stringify({}),
        },
      )
      let data = {}
      try {
        data = await response.json()
      } catch {
        data = {}
      }
      if (response.ok) {
        setNotice(
          data.detail ||
            'Контакты риэлтора отправлены в профиль — откройте вкладку «Уведомления».',
        )
        setDetailsProperty(null)
      } else if (response.status === 401 || response.status === 403) {
        setNotice(
          data.detail ||
            'Нужна авторизация клиента. Войдите по ссылке «Войти» выше (важно: тот же адрес, что и витрина — порт 5173), затем снова нажмите «К сделке».',
        )
      } else {
        setNotice(
          data.detail || `Не удалось отправить запрос (код ${response.status}).`,
        )
      }
    } catch {
      setNotice('Сеть недоступна или сервер не отвечает. Попробуйте позже.')
    } finally {
      setDealSubmitting(false)
    }
  }

  const togglePriceChat = () => {
    if (!detailsProperty) {
      return
    }
    if (!currentUser) {
      setAuthPromptKind('deal')
      setAuthPromptOpen(true)
      return
    }
    setPriceChatOpen((open) => !open)
  }

  const sendPriceChat = async () => {
    const text = priceChatInput.trim()
    if (!text || !detailsProperty?.id) {
      return
    }
    try {
      await fetch(`${API_BASE}/auth/csrf/`, { credentials: 'include' })
      const r = await fetch(`${API_BASE}/properties/${detailsProperty.id}/chat/`, {
        method: 'POST',
        credentials: 'include',
        headers: csrfHeaderObj(true),
        body: JSON.stringify({ message: text }),
      })
      const data = await r.json().catch(() => ({}))
      if (!r.ok) {
        setNotice(data.detail || 'Не удалось отправить сообщение.')
        return
      }
      setPriceChatInput('')
      setPriceChatMessages((prev) => {
        if (data.id != null && prev.some((x) => x.id === data.id)) {
          return prev
        }
        return [
          ...prev,
          {
            id: data.id,
            user: data.sender_username,
            text: data.body,
            created_at: data.created_at,
          },
        ]
      })
    } catch {
      setNotice('Сеть недоступна. Попробуйте ещё раз.')
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-brand">
          <p className="eyebrow">Агентство недвижимости</p>
          <h1>Real Estate Pro</h1>
          <p className="subtitle">
            Подбор жилой и коммерческой недвижимости, прозрачные условия и сопровождение на всех этапах
            сделки.
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
            {remoteProperties.length ? 'Каталог на сайте' : 'Демо-данные'}
          </span>
          {currentUser ? (
            <a
              className="ghost-link"
              href={backendHref('/profile/')}
              rel="noreferrer"
            >
              {currentUser.first_name || currentUser.username} · профиль
            </a>
          ) : (
            <a
              className="ghost-link"
              href={backendHref('/auth/login/')}
              rel="noreferrer"
            >
              Войти
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
              <h2>Real Estate Pro</h2>
            </div>
          </div>

          <div className="hero-intro-grid">
            <div className="hero-left-col">
              <div className="hero-copy">
                <p>
                  Мы помогаем клиентам купить, продать или снять недвижимость: от первого звонка до
                  передачи ключей. Работаем с жилыми и коммерческими объектами, подбираем варианты под
                  ваш бюджет и задачи.
                </p>
              </div>
              <WhyUsSection />
            </div>
            <div className="hero-gallery">
              <p className="section-label hero-gallery-label">Фотографии агентства</p>
              <div className="hero-gallery-stack">
                {companyGallery.length ? (
                  companyGallery.map((item) => (
                    <figure key={item.id} className="hero-gallery-figure">
                      <img src={item.image_url} alt={item.caption || 'Фото агентства'} />
                      {item.caption ? <figcaption>{item.caption}</figcaption> : null}
                    </figure>
                  ))
                ) : (
                  <>
                    <img className="hero-gallery-img-fill" src={PLACEHOLDER_IMG} alt="Недвижимость" />
                    <img className="hero-gallery-img-fill" src={PLACEHOLDER_IMG} alt="Объект" />
                    <img className="hero-gallery-img-fill" src={PLACEHOLDER_IMG} alt="Агентство" />
                  </>
                )}
              </div>
              <div className="hero-gallery-cta">
                <p className="hero-gallery-cta-text">
                  Актуальные предложения, карта и фильтры — в каталоге.
                </p>
                <button
                  type="button"
                  className="hero-gallery-cta-button"
                  onClick={() => setActiveView('market')}
                >
                  Открыть объекты
                </button>
              </div>
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
              <span>Каталог</span>
              <strong>{loading ? 'Загрузка...' : 'Обновлён'}</strong>
            </div>
          </div>
        </section>
        )}

        {activeView === 'market' && (
        <section className="content-grid">
          <aside className="panel filters-panel">
            <div className="filters-head">
              <div className="filters-head-text">
                <p className="section-label">Поиск</p>
                <h2>Фильтры</h2>
              </div>
              <button type="button" className="filters-reset-button" onClick={resetFilters}>
                Сбросить фильтры
              </button>
            </div>

            <label className="field">
              <span>Тип сделки</span>
              <select
                value={filters.deal}
                onChange={(event) =>
                  setFilters((current) => ({
                    ...current,
                    deal: event.target.value,
                  }))
                }
              >
                <option value="all">Все сделки</option>
                <option value="sale">Только продажа</option>
                <option value="rent">Только аренда</option>
              </select>
            </label>

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
                <div className="empty-state">Загружаем каталог...</div>
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
                        setDetailSessionKey((k) => k + 1)
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
              <h2>Расположение объектов</h2>
            </div>
            <span className="result-count">
              {selectedProperty ? selectedProperty.title : 'Нет объекта'}
            </span>
          </div>

          <div className="map-box">
            <YandexMap
              className="yandex-map"
              center={mapCenter}
              zoom={12}
              markers={catalogMapMarkers}
              onMarkerClick={(id) => setSelectedPropertyId(id)}
            />
          </div>
        </section>
        )}

        {activeView === 'analytics' && (
        <section className="analytics-panel panel">
          <div className="section-head compact analytics-section-head">
            <div>
              <p className="section-label">Аналитика</p>
              <h2>Спрос и предложение</h2>
              <p className="analytics-lead">
                Сводка по каталогу и обращениям: доли сделок, средние значения и распределение по
                городам и типам объектов.
              </p>
            </div>
            <span className="analytics-pill">По данным текущей базы</span>
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

          <div className="analytics-grid">
            <div className="analytics-card">
              <span>Активные объявления</span>
              <strong>{activeCount}</strong>
              <p>
                {totalCount > 0
                  ? `${activeSharePct}% от всех карточек в базе`
                  : 'Нет объектов для расчёта доли'}
              </p>
            </div>
            <div className="analytics-card">
              <span>Продажа</span>
              <strong>{saleCount}</strong>
              <p>
                {totalCount > 0 ? `${saleSharePct}% от каталога` : '—'}
              </p>
            </div>
            <div className="analytics-card">
              <span>Аренда</span>
              <strong>{rentCount}</strong>
              <p>
                {totalCount > 0 ? `${rentSharePct}% от каталога` : '—'}
              </p>
            </div>
            <div className="analytics-card">
              <span>В топе / избранном</span>
              <strong>{featuredCount}</strong>
              <p>Объектов с пометкой «избранное» у агентства</p>
            </div>
          </div>

          <div className="analytics-grid">
            <div className="analytics-card">
              <span>Новые заявки (статус)</span>
              <strong>{newInq}</strong>
              <p>Ожидают первичной обработки</p>
            </div>
            <div className="analytics-card">
              <span>В работе</span>
              <strong>{inProgressInq}</strong>
              <p>Заявки в активной стадии</p>
            </div>
            <div className="analytics-card">
              <span>Средняя цена за м²</span>
              <strong>{pricePerSqm ? formatMoney(pricePerSqm) : '—'}</strong>
              <p>От средней цены и площади по базе</p>
            </div>
            <div className="analytics-card">
              <span>Обращений на объект</span>
              <strong>{inquiriesPerListing ?? '—'}</strong>
              <p>Среднее число заявок на одну карточку</p>
            </div>
          </div>

          <div className="analytics-mix-block">
            <div className="analytics-mix-head">
              <h3 className="analytics-mix-title">Структура каталога</h3>
              <p className="analytics-mix-sub">
                Соотношение продажи и аренды по числу объектов — удобно оценить фокус базы.
              </p>
            </div>
            <div
              className="analytics-mix-bar"
              role="img"
              aria-label={`Продажа ${saleSharePct} процентов, аренда ${rentSharePct} процентов`}
            >
              {totalCount > 0 ? (
                <>
                  <span
                    className="analytics-mix-seg analytics-mix-seg--sale"
                    style={{ width: `${saleSharePct}%` }}
                  />
                  <span
                    className="analytics-mix-seg analytics-mix-seg--rent"
                    style={{ width: `${rentSharePct}%` }}
                  />
                </>
              ) : (
                <span className="analytics-mix-empty">Нет объектов в выборке</span>
              )}
            </div>
            <div className="analytics-mix-legend">
              <span>
                <i className="analytics-dot analytics-dot--sale" /> Продажа — {saleCount} (
                {saleSharePct}%)
              </span>
              <span>
                <i className="analytics-dot analytics-dot--rent" /> Аренда — {rentCount} (
                {rentSharePct}%)
              </span>
            </div>
          </div>

          <div className="analytics-insights">
            <article className="analytics-insight-card">
              <h3>Нагрузка на каталог</h3>
              <p>
                {inquiryCount > 0 && totalCount > 0
                  ? `На каждую карточку приходится в среднем ${inquiriesPerListing} обращений — это помогает понять интерес аудитории к текущему предложению.`
                  : 'Как только в базе появятся объекты и заявки, здесь появится оценка интереса к каталогу.'}
              </p>
            </article>
            <article className="analytics-insight-card">
              <h3>Динамика цен за месяц</h3>
              <p>
                {avgPriceAll > 0
                  ? `Средняя цена среди объектов, добавленных за 30 дней, ${priceDelta >= 0 ? 'выше' : 'ниже'} общей средней по базе на ${Math.abs(priceDelta)}%. Показатель ориентировочный и зависит от состава новых лотов.`
                  : 'Недостаточно данных для сравнения средних цен.'}
              </p>
            </article>
            <article className="analytics-insight-card">
              <h3>Спрос в работе</h3>
              <p>
                {inquiryCount > 0
                  ? `Из ${inquiryCount} обращений ${newInq} со статусом «новая» и ${inProgressInq} находятся в работе — видно, насколько команда успевает обрабатывать поток.`
                  : 'Заявок пока нет — блок заполнится после появления обращений в CRM.'}
              </p>
            </article>
            <article className="analytics-insight-card">
              <h3>География и типы</h3>
              <p>
                Ниже — распределение объектов по городам и типам недвижимости и заявок по городам.
                Сравните столбцы: где больше предложения, а где — входящих заявок.
              </p>
            </article>
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
                {(() => {
                  const galleryList = Array.isArray(detailsProperty.images)
                    ? detailsProperty.images.filter(Boolean)
                    : []
                  const slides =
                    galleryList.length > 0
                      ? galleryList
                      : [{ image_url: PLACEHOLDER_IMG, id: 'placeholder' }]
                  const safeIndex = Math.min(detailsPhotoIndex, Math.max(slides.length - 1, 0))
                  const currentSrc = slides[safeIndex]?.image_url || PLACEHOLDER_IMG
                  const step = (delta) => {
                    if (slides.length < 2) return
                    setDetailsPhotoIndex((i) => (i + delta + slides.length) % slides.length)
                  }
                  return (
                    <div className="details-photos-top">
                      <div
                        className="details-photo-carousel"
                        onTouchStart={(e) => {
                          detailsSwipeRef.current.x = e.touches[0].clientX
                        }}
                        onTouchEnd={(e) => {
                          if (slides.length < 2) return
                          const dx = e.changedTouches[0].clientX - detailsSwipeRef.current.x
                          if (dx > 48) step(-1)
                          else if (dx < -48) step(1)
                        }}
                      >
                        <div className="details-photo-frame">
                          {slides.length > 1 && (
                            <button
                              type="button"
                              className="details-photo-nav details-photo-nav--prev"
                              aria-label="Предыдущее фото"
                              onClick={(e) => {
                                e.stopPropagation()
                                step(-1)
                              }}
                            >
                              ‹
                            </button>
                          )}
                          <img
                            className="details-photo-main"
                            src={currentSrc}
                            alt={slides[safeIndex]?.caption || detailsProperty.title}
                          />
                          {slides.length > 1 && (
                            <button
                              type="button"
                              className="details-photo-nav details-photo-nav--next"
                              aria-label="Следующее фото"
                              onClick={(e) => {
                                e.stopPropagation()
                                step(1)
                              }}
                            >
                              ›
                            </button>
                          )}
                          {slides.length > 1 && (
                            <span className="details-photo-counter">
                              {safeIndex + 1} / {slides.length}
                            </span>
                          )}
                        </div>
                        {slides.length > 1 && (
                          <div className="details-gallery-thumbs" role="tablist">
                            {slides.map((img, idx) => (
                              <button
                                key={img.id || img.image_url || idx}
                                type="button"
                                className={`details-thumb-btn ${idx === safeIndex ? 'details-thumb-btn--active' : ''}`}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setDetailsPhotoIndex(idx)
                                }}
                                aria-label={`Фото ${idx + 1}`}
                              >
                                <img
                                  src={img.image_url || PLACEHOLDER_IMG}
                                  alt=""
                                  className="details-gallery-thumb"
                                />
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })()}
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
                  <div className="details-action-buttons">
                    <button
                      type="button"
                      className="deal-interest-button"
                      disabled={dealSubmitting}
                      onClick={handleDealInterest}
                    >
                      {dealSubmitting ? 'Отправка…' : 'К сделке'}
                    </button>
                    <button type="button" className="nav-btn-secondary" onClick={togglePriceChat}>
                      {priceChatOpen ? 'Закрыть чат' : 'Спросить о цене'}
                    </button>
                    <button
                      type="button"
                      className={`favorite-button ${
                        favoritePropertyIds.includes(detailsProperty.id)
                          ? 'favorite-button--active'
                          : ''
                      }`}
                      onClick={() => toggleFavorite(detailsProperty.id)}
                    >
                      {favoritePropertyIds.includes(detailsProperty.id)
                        ? 'В избранном'
                        : 'В избранное'}
                    </button>
                  </div>
                  <p className="details-deal-hint">
                    После запроса контакты риэлтора появятся в вашем профиле в разделе уведомлений.
                  </p>
                  {priceChatOpen && (
                    <div className="price-chat-panel">
                      <p className="section-label">Чат с риэлтором по объекту</p>
                      <div className="price-chat-messages">
                        {priceChatMessages.length === 0 ? (
                          <p className="muted">
                            Сообщения сохраняются и приходят риэлтору в уведомления и во вкладку «Чаты с клиентами» в кабинете.
                          </p>
                        ) : (
                          priceChatMessages.map((row, idx) => (
                            <div
                              key={row.id != null ? `m-${row.id}` : `m-${row.user}-${idx}`}
                              className="price-chat-row"
                            >
                              <strong>{row.user}:</strong> {row.text}
                            </div>
                          ))
                        )}
                      </div>
                      <div className="price-chat-input-row">
                        <input
                          type="text"
                          className="field-input"
                          value={priceChatInput}
                          onChange={(e) => setPriceChatInput(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && sendPriceChat()}
                          placeholder="Ваше сообщение…"
                          maxLength={2000}
                        />
                        <button
                          type="button"
                          className="primary-link-button"
                          onClick={sendPriceChat}
                        >
                          Отправить
                        </button>
                      </div>
                    </div>
                  )}
                </div>
                {remoteProperties.length > 0 && similarProperties.length > 0 && (
                  <div className="similar-properties-block">
                    <p className="section-label">Похожие объекты</p>
                    <p className="similar-properties-hint">
                      Подбор по городу, комнатам, цене, этажу и близости к тем же станциям метро.
                    </p>
                    <div className="similar-properties-grid">
                      {similarProperties.map((s) => (
                        <button
                          key={s.id}
                          type="button"
                          className="similar-property-card"
                          onClick={async () => {
                            const full = await fetchJson(`${API_BASE}/properties/${s.id}/`)
                            if (full?.id) {
                              setDetailsProperty(full)
                              setDetailSessionKey((k) => k + 1)
                            }
                          }}
                        >
                          <img
                            className="similar-property-img"
                            src={s.image_url || PLACEHOLDER_IMG}
                            alt=""
                          />
                          <div className="similar-property-body">
                            <span className={`badge ${s.deal_type}`}>
                              {s.deal_type === 'sale' ? 'Продажа' : 'Аренда'}
                            </span>
                            <strong>{s.title}</strong>
                            <span>
                              {s.city_name} · {s.rooms ?? '—'} комн. ·{' '}
                              {s.floor != null ? `${s.floor} эт.` : 'этаж —'}
                            </span>
                            <span className="similar-property-price">{formatMoney(s.price)}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <aside className="details-side">
                <h3>Местоположение на карте</h3>
                <div className="details-map-box">
                  <YandexMap
                    className="yandex-map yandex-map--compact"
                    center={detailsMapCenter}
                    zoom={13}
                    markers={detailsMapMarkers}
                  />
                </div>
              </aside>
            </div>
          </div>
        </div>
      )}
      {authPromptOpen && (
        <div className="details-modal-backdrop" onClick={closeAuthPrompt}>
          <div
            className="details-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="details-modal-header">
              <div>
                <p className="section-label">Только для авторизованных</p>
                {authPromptKind === 'deal' ? (
                  <>
                    <h2>Зарегистрируйтесь, чтобы перейти к сделке</h2>
                    <p className="subtitle">
                      Мы отправим контакты ответственного риэлтора и сводку по объекту в раздел
                      «Уведомления» вашего профиля — так данные не светятся публично в каталоге.
                    </p>
                  </>
                ) : (
                  <>
                    <h2>Войдите, чтобы добавить в избранное</h2>
                    <p className="subtitle">
                      Сохранённые объекты будут доступны в вашем личном кабинете.
                    </p>
                  </>
                )}
              </div>
              <button type="button" className="ghost-link" onClick={closeAuthPrompt}>
                Закрыть
              </button>
            </div>
            <div className="auth-prompt-actions">
              <a
                href={backendHref('/auth/login/')}
                className="primary-link-button"
              >
                Войти
              </a>
              <a
                href={backendHref('/auth/register/')}
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

