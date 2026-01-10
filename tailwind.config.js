/**
 * Tailwind CSS v4 Configuration
 *
 * Tailwind v4 uses CSS-based configuration via @theme in input.css
 * This file only specifies:
 * - Content paths for class detection
 * - Typography plugin configuration
 *
 * All theme customization (colors, fonts, shadows, animations) is in:
 * app/static/css/input.css (@theme block)
 */

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/templates/**/*.html"],
  plugins: [],
}
