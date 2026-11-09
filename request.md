# Refactor frontend follow MVVM pattern:
- use flet instead tkinter
- use flet command instead traditional function call
- use flet property binding instead traditional property setting

# Note:
- flet new version syntax (flet==0.86.1) (Ex: Colors instead colors)
- improve feature, no need keep style and UI UX, follow flet best practice
- use clean code principle

# Expectation:
- improve feature, make it modern and user-friendly
- modern UI UX

# Refactor DB connection/user/password
- when start app, app should run check DB connection first
- if DB connection is not available, show error message and retry/config DB dialog
- if DB connection is available, show success message and continue to Login page,
in login page should have config DB button to config DB