# Project Scratchpad

This file will be used to jot down notes, ideas, and plans for improving the project.

## Current Architecture Analysis

### Backend
- Flask web application
- SQLite database (birdnames.db, speciesid.db)
- TensorFlow Lite model integration
- Frigate integration for camera/video
- REST endpoints for:
  - Bird detections
  - Image/video retrieval
  - Daily summaries
  - Hourly statistics

### Frontend
- Vue 2.6.14 (browser import)
- Bootstrap 5.1.3
- jQuery dependency
- Mixed template rendering (Jinja2 + Vue)
- Single Vue component (RecentDetections)

## Vue 3 Upgrade Plan

### Phase 1: Setup Modern Build System
- [ ] Initialize Vue 3 with Vite
- [ ] Setup TypeScript support
- [ ] Configure build process for Docker integration
- [ ] Setup ESLint + Prettier
- [ ] Configure Vue Router
- [ ] Setup Pinia for state management

### Phase 2: Component Migration
- [ ] Convert existing templates to Vue components:
  - [ ] RecentDetections (upgrade existing)
  - [ ] DailySummary
  - [ ] DetectionsByHour
  - [ ] DetectionsByScientificName
  - [ ] Navigation
  - [ ] DatePicker
- [ ] Create shared components:
  - [ ] ImageViewer (for thumbnails/snapshots)
  - [ ] VideoPlayer (for clips)
  - [ ] DataTable (reusable table component)
  - [ ] StatisticsCard

### Phase 3: State Management & API Integration
- [ ] Setup API module structure
- [ ] Implement Pinia stores:
  - [ ] detections (recent, by hour, by species)
  - [ ] dailySummary
  - [ ] mediaAssets (images/videos)
  - [ ] filters (date, species)
- [ ] Add real-time updates capability
- [ ] Implement proper error handling
- [ ] Add loading states

### Phase 4: UI/UX Improvements
- [ ] Implement responsive grid layout
- [ ] Add transitions/animations
- [ ] Improve image/video viewer
- [ ] Add dark mode support
- [ ] Implement infinite scroll for detections
- [ ] Add filter/search capabilities
- [ ] Implement data visualization (charts/graphs)

### Phase 5: Performance Optimization
- [ ] Setup proper code splitting
- [ ] Implement lazy loading for routes
- [ ] Add service worker for offline support
- [ ] Optimize image loading
- [ ] Add proper caching strategy
- [ ] Implement virtual scrolling for large datasets

## Docker Integration Notes

- Current setup uses port 7766
- Need to configure Vite dev server
- Consider multi-stage build for production
- Setup volume mounts for development
- Configure hot reload for development

## API Endpoints to Create/Modify

- [ ] GET /api/detections/recent
- [ ] GET /api/detections/daily-summary
- [ ] GET /api/detections/by-hour
- [ ] GET /api/detections/by-species
- [ ] GET /api/media/thumbnail/:id
- [ ] GET /api/media/snapshot/:id
- [ ] GET /api/media/clip/:id

## Ideas for Future Enhancement

### Completed Features
1. Real-time WebSocket Integration ✅
   - Live bird detection notifications
   - Instant UI updates without polling
   - Connection status indicator
   - Reconnection handling

2. Weather Integration (Phase 1 & 2) ✅
   - OpenWeatherMap API integration
   - Weather data collection and storage
   - Basic pattern analysis and insights
   - Current weather display
   - Unit system configuration (°F/mph or °C/m/s)

### Immediate Priority Features
1. Weather Integration (Phase 3 & 4) 🚧
   - Advanced weather pattern analysis
   - Weather overlay on activity charts
   - Correlation visualizations
   - Forecast-based predictions
   - Weather-based notifications

2. Enhanced Data Visualization
   - Daily/weekly/monthly bird visit patterns
   - Species frequency charts
   - Peak activity time analysis
   - Interactive timeline view
   - Heatmap of detection times
   - D3.js or Chart.js integration

3. Modern UI/UX Improvements
   - Material Design 3 or Tailwind UI
   - Smooth transitions and animations
   - Skeleton loading states
   - Toast notifications for new detections
   - Gesture support for image viewing
   - Infinite scroll for detection history

4. Progressive Web App Features
   - Offline support
   - Push notifications
   - Home screen installation
   - Background sync
   - Cache management
   - App shell architecture

5. Mobile-First Responsive Design
   - Touch-friendly interfaces
   - Swipe gestures
   - Responsive image galleries
   - Mobile-optimized video player
   - Adaptive layout components

### Future Enhancements
- Species comparison views
- Time-lapse generation
- Export capabilities (CSV, PDF reports)
- Machine learning insights (visiting patterns, behavior analysis)
- Social sharing features
- Weather correlation analysis
- Custom alert configurations
- Mobile app integration

## Classification Debugging (2025-01-17)

### Recent Changes (2025-01-18)
1. Added detailed TensorFlow model output logging
   - Full category object inspection
   - Display name and category name analysis
   - Better common name extraction
   - Improved error tracing

2. Development workflow improvements
   - Added hot reloading for Python files
   - Mounted source files in Docker
   - Flask debug mode enabled
   - Uvicorn auto-reload configured

3. Fixed weather patterns endpoint
   - Proper cursor initialization
   - Improved SQLite datetime handling
   - Better error messages
   - Added data validation checks

4. Enhanced error handling
   - More detailed error logging
   - Better error messages in UI
   - Improved error recovery
   - Full stack traces in logs

### Next Steps
1. Monitor logs for:
   - TensorFlow model name fields
   - Common name vs scientific name handling
   - Classification confidence patterns
   - Any error patterns

2. Potential areas to investigate:
   - Model output structure
   - Name field mappings
   - Error handling improvements
   - Performance optimizations

## Technical Debt to Address

High Priority:
- Remove jQuery dependency
- Implement Tailwind CSS
- Setup proper TypeScript types and interfaces
- Add comprehensive error handling
- Add WebSocket support for real-time updates
- Implement proper loading states and error boundaries
- Setup proper code splitting and lazy loading

Medium Priority:
- Improve test coverage (Vitest + Vue Test Utils)
- Setup CI/CD pipeline (GitHub Actions)
- Add E2E testing with Cypress
- Implement proper logging
- Setup monitoring and analytics
- Add performance monitoring
- Implement proper security headers

Low Priority:
- Setup documentation generation
- Add accessibility testing
- Implement API versioning
- Setup development guidelines
- Add contribution guidelines
