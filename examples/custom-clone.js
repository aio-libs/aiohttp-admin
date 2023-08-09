export const g = {"Queue": null, "Link": null, "stringify": null, "Button": null,
                  "createElement": null, "useRecordContext": null, "useCreatePath": null,
                  "useResourceContext": null}

const CustomCloneButton = (props) => {
    const {
        label = "My custom clone",
        scrollToTop = true,
        icon = g.createElement(g.Queue),
        ...rest
    } = props;
    const resource = g.useResourceContext(props);
    const record = g.useRecordContext(props);
    const createPath = g.useCreatePath();
    const pathname = createPath({resource, type: "create"});
    props = {
        component: g.Link,
        to: (
            record
                ? {
                      pathname,
                      search: g.stringify({source: JSON.stringify(record)}),
                      state: {_scrollToTop: scrollToTop},
                  }
                : pathname
        ),
        label: label,
        onClick: stopPropagation,
        ...sanitizeRestProps(rest)
    };
    return g.createElement(g.Button, props, icon);
};

// useful to prevent click bubbling in a datagrid with rowClick
const stopPropagation = e => e.stopPropagation();

const sanitizeRestProps = ({resource, record, ...rest}) => rest;

export const components = {CustomCloneButton: CustomCloneButton};
