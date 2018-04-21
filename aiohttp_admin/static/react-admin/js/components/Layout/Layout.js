import { Layout } from 'admin-on-rest';
import getMuiTheme from 'material-ui/styles/getMuiTheme';
import { indigo500, indigo700, redA200 } from 'material-ui/styles/colors';


const muiTheme = getMuiTheme({
  palette: {
    primary1Color: indigo500,
    primary2Color: indigo700,
    primary3Color: indigo700,
    accent1Color: redA200,
    pickerHeaderColor: indigo500,
  }
});


Layout.defaultProps = {
  theme: muiTheme
};

export default Layout;
