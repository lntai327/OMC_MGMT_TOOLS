# App Architecture
- Strict separate concern
- Frontend
  - MVVM (Model-View-ViewModel)
- Backend
  - Clean Architecture (Service-Repository pattern)
- Database
  - sqlalchemy, sqlserver

# Performance and user experience
- Loading Screen & Startup
  - Verify app launches cleanly with loading UI instead of hanging on a black screen during startup.
  - Verify loading spinner is visible during Excel export and DB loading.

# Tech Stack
- Frontend
  - python (GUI library : Flet)
- Backend
  - python
- excel : library openpyxl