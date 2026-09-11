// Único lugar donde el Angular sabe dónde vive el backend. apiUrl la usan
// authInterceptor (agrega el JWT) y error.interceptor (muestra el error) en
// cada HttpClient.get/post/... de la app -- ningún componente arma la URL a
// mano. Este archivo (`ng serve`) apunta al backend local; el build de
// producción usa environment.ts, con la URL de Railway. El backend, a su
// vez, solo acepta peticiones de este origin si está en CORS_ORIGINS
// (backend/app/core/config.py) -- en local coincide con localhost:4200.
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1',
  primeuiLicense:
    'eyJpZCI6IjAzNjE2ODM4LTU4NTktNGVlOC1iZDVlLTI1ZTBlZjU1YzFlZiIsInByb2R1Y3QiOiJwcmltZXVpIiwidGllciI6ImNvbW11bml0eSIsInR5cGUiOiJkZXYiLCJpYXQiOjE3ODg0MzcyMzYsImV4cCI6MTgxOTk3MzIzNn0.lQq8X44cgVsOFdC4Q1OALL1FdVApsiAM0oBAu2QSLPG1hIWUFacPuMxwTiJoS3naQtjnjDkSVCeKC19zA3M3Bw',
};
