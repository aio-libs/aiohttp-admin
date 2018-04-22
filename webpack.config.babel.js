const path = 'aiohttp_admin/static/react-admin';


export default {
  entry: [
    `./${path}/js/index.jsx`
  ],
  output: {
    path: __dirname + `/${path}/dist`,
    filename: 'bundle.js'
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: ['babel-loader']
      },
      { test: /\.sass/,
        use: [
          { loader: 'style-loader' },
          { loader: 'css-loader' },
          { loader: 'sass-loader' }
        ]
      },
    ]
  },
  resolve: {
    extensions: ['*', '.js', '.jsx']
  }
};
