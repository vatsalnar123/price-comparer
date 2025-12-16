import { useState } from 'react'

// API base: /api for Vercel production, localhost for development
const API_BASE = import.meta.env.PROD ? '/api' : 'http://127.0.0.1:8000'

function App() {
  const [address1, setAddress1] = useState('')
  const [address2, setAddress2] = useState('')
  const [comparison, setComparison] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleCompare = async (e) => {
    e.preventDefault()
    
    if (!address1.trim() || !address2.trim()) {
      setError('Please enter both property addresses')
      return
    }
    
    try {
      setLoading(true)
      setError(null)
      
      const res = await fetch(`${API_BASE}/compare-addresses`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          address_1: address1.trim(),
          address_2: address2.trim(),
        }),
      })
      
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to compare properties')
      }
      
      const data = await res.json()
      setComparison(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const resetComparison = () => {
    setComparison(null)
    setError(null)
  }

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(price)
  }

  const calculateDiff = (listed, predicted) => {
    const diff = predicted - listed
    const percent = ((diff / listed) * 100).toFixed(1)
    return { diff, percent }
  }

  // Sample addresses for quick testing
  const sampleAddresses = [
    "123 Park Avenue, New York, NY",
    "456 Ocean Drive, Miami, FL",
    "789 Market Street, San Francisco, CA",
    "321 Lake Shore Drive, Chicago, IL",
    "555 Sunset Boulevard, Los Angeles, CA",
    "888 Congress Avenue, Austin, TX",
  ]

  if (comparison) {
    return (
      <div className="app">
        <button className="back-btn" onClick={resetComparison}>
          ← Compare Different Addresses
        </button>
        
        <div className="comparison-results">
          <div className="comparison-header">
            <h2>Property Comparison</h2>
            <p style={{ color: 'var(--color-text-muted)' }}>
              Side-by-side analysis with ML-predicted prices
            </p>
          </div>
          
          <div className="comparison-grid">
            <PropertyCard property={comparison.property_1} formatPrice={formatPrice} calculateDiff={calculateDiff} />
            <PropertyCard property={comparison.property_2} formatPrice={formatPrice} calculateDiff={calculateDiff} />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Property Comparison</h1>
        <p>Enter two property addresses to compare their features and predicted prices</p>
      </header>
      
      <form className="address-form" onSubmit={handleCompare}>
        <div className="address-inputs">
          <div className="address-panel">
            <label className="address-label">Property 1 Address</label>
            <input
              type="text"
              className="address-input"
              placeholder="e.g., 123 Main St, New York, NY"
              value={address1}
              onChange={(e) => setAddress1(e.target.value)}
            />
            <div className="sample-addresses">
              <span className="sample-label">Try:</span>
              {sampleAddresses.slice(0, 3).map((addr, i) => (
                <button
                  key={i}
                  type="button"
                  className="sample-btn"
                  onClick={() => setAddress1(addr)}
                >
                  {addr.split(',')[0]}
                </button>
              ))}
            </div>
          </div>
          
          <div className="vs-divider">
            <div className="vs-badge">VS</div>
          </div>
          
          <div className="address-panel">
            <label className="address-label">Property 2 Address</label>
            <input
              type="text"
              className="address-input"
              placeholder="e.g., 456 Oak Ave, Los Angeles, CA"
              value={address2}
              onChange={(e) => setAddress2(e.target.value)}
            />
            <div className="sample-addresses">
              <span className="sample-label">Try:</span>
              {sampleAddresses.slice(3, 6).map((addr, i) => (
                <button
                  key={i}
                  type="button"
                  className="sample-btn"
                  onClick={() => setAddress2(addr)}
                >
                  {addr.split(',')[0]}
                </button>
              ))}
            </div>
          </div>
        </div>
        
        <button 
          type="submit"
          className="compare-btn" 
          disabled={loading || !address1.trim() || !address2.trim()}
        >
          {loading ? (
            <>
              <span className="btn-spinner"></span>
              Comparing...
            </>
          ) : (
            'Compare Properties'
          )}
        </button>
      </form>
      
      {error && (
        <div className="error">
          <p>{error}</p>
          <p style={{ marginTop: '0.5rem', fontSize: '0.9rem', opacity: 0.8 }}>
            Make sure the backend is running at {API_BASE}
          </p>
        </div>
      )}
      
      <div className="info-section">
        <h3>How it works</h3>
        <div className="info-grid">
          <div className="info-card">
            <div className="info-icon">🏠</div>
            <h4>Enter Addresses</h4>
            <p>Type any two property addresses you want to compare</p>
          </div>
          <div className="info-card">
            <div className="info-icon">📊</div>
            <h4>Get Mock Data</h4>
            <p>Property features are simulated based on location characteristics</p>
          </div>
          <div className="info-card">
            <div className="info-icon">🤖</div>
            <h4>ML Prediction</h4>
            <p>Our model predicts estimated property values based on features</p>
          </div>
        </div>
      </div>
    </div>
  )
}

function PropertyCard({ property, formatPrice, calculateDiff }) {
  const { diff, percent } = calculateDiff(property.listed_price, property.predicted_price)
  const isOvervalued = diff < 0
  
  return (
    <div className="property-card">
      <img className="property-card-image" src={property.image_url} alt={property.title} />
      <div className="property-card-content">
        <h3 className="property-card-title">{property.title}</h3>
        
        {property.address && (
          <div className="property-card-address">{property.address}</div>
        )}
        
        <div className="property-card-location">{property.location}</div>
        
        <div className="price-section">
          <div className="price-box">
            <div className="price-label">Estimated Market Price</div>
            <div className="price-value listed">{formatPrice(property.listed_price)}</div>
          </div>
          <div className="price-box">
            <div className="price-label">AI Predicted Value</div>
            <div className="price-value predicted">{formatPrice(property.predicted_price)}</div>
            <div className={`price-diff ${isOvervalued ? 'negative' : 'positive'}`}>
              {isOvervalued ? '↓' : '↑'} {Math.abs(percent)}% ({formatPrice(Math.abs(diff))})
            </div>
          </div>
        </div>
        
        <div className="features-grid">
          <div className="feature-item">
            <div className="feature-icon">🛏️</div>
            <div className="feature-value">{property.bedrooms}</div>
            <div className="feature-label">Beds</div>
          </div>
          <div className="feature-item">
            <div className="feature-icon">🛁</div>
            <div className="feature-value">{property.bathrooms}</div>
            <div className="feature-label">Baths</div>
          </div>
          <div className="feature-item">
            <div className="feature-icon">📐</div>
            <div className="feature-value">{property.size_sqft.toLocaleString()}</div>
            <div className="feature-label">Sq Ft</div>
          </div>
        </div>
        
        <div className="details-list">
          <div className="detail-row">
            <span className="detail-label">Property Type</span>
            <span className="detail-value">{property.property_type === 'SFH' ? 'Single Family' : 'Condo'}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Year Built</span>
            <span className="detail-value">{property.year_built}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">School Rating</span>
            <span className="detail-value">{'⭐'.repeat(Math.min(5, Math.ceil(property.school_rating / 2)))} {property.school_rating}/10</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Pool</span>
            <span className={`detail-value ${property.has_pool ? 'yes' : 'no'}`}>
              {property.has_pool ? '✓ Yes' : '✗ No'}
            </span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Garage</span>
            <span className={`detail-value ${property.has_garage ? 'yes' : 'no'}`}>
              {property.has_garage ? '✓ Yes' : '✗ No'}
            </span>
          </div>
        </div>
        
        {property.amenities && property.amenities.length > 0 && (
          <div className="amenities">
            <div className="amenities-label">Amenities</div>
            <div className="amenities-list">
              {property.amenities.map((amenity, i) => (
                <span key={i} className="amenity-tag">{amenity}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
