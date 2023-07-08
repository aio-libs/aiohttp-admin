import * as React from 'react';
import { memo } from 'react';
import Queue from '@mui/icons-material/Queue';
import { Link } from 'react-router-dom';
import { stringify } from 'query-string';

import { Button, ButtonProps, useRecordContext, useCreatePath } from 'react-admin';

const CopyUserButton = (props) => {
    const {
        label = 'ra.action.clone',
        scrollToTop = true,
        icon = defaultIcon,
        ...rest
    } = props;
    const record = useRecordContext(props);
    const createPath = useCreatePath();
    const pathname = createPath({ resource: 'User', type: 'create' });
    return (
        <Button
            component={Link}
            to={
                record
                    ? {
                          pathname,
                          search: stringify({
                              source: JSON.stringify(record),
                          }),
                          state: { _scrollToTop: scrollToTop },
                      }
                    : pathname
            }
            label={label}
            onClick={stopPropagation}
            {...sanitizeRestProps(rest)}
        >
            {icon}
        </Button>
    );
};

const defaultIcon = <Queue />;

// useful to prevent click bubbling in a datagrid with rowClick
const stopPropagation = e => e.stopPropagation();

const sanitizeRestProps = ({resource, record, ...rest}) => rest;

export const components = {CopyUserButton: memo(CopyUserButton)};
