'use strict'
module.exports = {
  NODE_ENV: '"production"',
  BACKEND_HOST: JSON.stringify(process.env.BACKEND_HOST),
  BACKEND_PORT: JSON.stringify(process.env.BACKEND_PORT),
  TUSD_HOST: JSON.stringify(process.env.TUSD_HOST),
  TUSD_PORT: JSON.stringify(process.env.TUSD_PORT),
}
