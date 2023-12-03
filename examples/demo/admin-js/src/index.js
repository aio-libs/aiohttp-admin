import { memo } from 'react';
import Queue from '@mui/icons-material/Queue';
import { Link } from 'react-router-dom';
import { stringify } from 'query-string';
import { useResourceContext, useRecordContext, useCreatePath, Button } from 'react-admin';

export const CustomCloneButton = (props: CloneButtonProps) => {
    const {
        label = 'CUSTOM CLONE',
        scrollToTop = true,
        icon = defaultIcon,
        ...rest
    } = props;
    const resource = useResourceContext(props);
    const record = useRecordContext(props);
    const createPath = useCreatePath();
    const pathname = createPath({ resource, type: 'create' });
    return (
        <Button
            component={Link}
            to={
                record
                    ? {
                          pathname,
                          search: stringify({
                              source: JSON.stringify(omitId(record)),
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

const stopPropagation = e => e.stopPropagation();

const omitId = ({ id, ...rest }) => rest;

const sanitizeRestProps = ({
    resource,
    record,
    ...rest
}) => rest;

export const components = {CustomCloneButton: memo(CustomCloneButton)};
