import axios from 'axios'

// Create axios instance with base URL
const api = axios.create({
  // Always use relative URLs to ensure requests go through Vite's proxy
  baseURL: '',
  // Ensure proper headers are set
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }
})

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    // Log the full URL being requested
    console.debug('Making request to:', {
      url: config.url || '',
      baseURL: config.baseURL || '',
      method: config.method,
      headers: config.headers
    })
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.debug('Received response:', {
      status: response.status,
      headers: response.headers,
      url: response.config.url || ''
    })
    return response
  },
  (error) => {
    console.error('API Response Error:', {
      message: error.message,
      config: error.config,
      response: error.response
    })
    return Promise.reject(error)
  }
)

export default api
