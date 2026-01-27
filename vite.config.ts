import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
      manifest: {
        name: 'OdontoSys - Gestão Inteligente',
        short_name: 'OdontoSys',
        description: 'Sistema de Gestão para Clínicas Odontológicas',
        theme_color: '#2563eb', // Cor azul do seu tema
        background_color: '#ffffff',
        display: 'standalone', // Isso faz parecer aplicativo (sem barra de URL)
        icons: [
          {
            src: 'pwa-192x192.png', // Você precisará criar esses ícones depois
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    })
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        secure: false,
      },
      '/auth': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
});