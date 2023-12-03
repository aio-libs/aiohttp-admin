module.exports = {
  webpack: {
    configure: {
      output: {
        library: {
          type: 'module'
        }
      },
      experiments: {outputModule: true}
    }
  }
}
