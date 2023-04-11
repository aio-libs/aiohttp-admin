import {
    Admin, Create, Datagrid, DatagridConfigurable, Edit, EditButton, List, HttpError, Resource, SimpleForm,
    SelectColumnsButton, CreateButton, FilterButton, ExportButton, TopToolbar,
    AppBar, InspectorButton, Layout, TitlePortal,
    BulkDeleteButton, BulkExportButton, BulkUpdateButton,
    SimpleShowLayout, Show,
    AutocompleteInput,
    BooleanField, BooleanInput,
    DateField, DateInput,
    NumberField, NumberInput,
    ReferenceField, ReferenceInput as _ReferenceInput,
    ReferenceManyField,
    SelectInput,
    TextField, TextInput,
    WithRecord, required
} from "react-admin";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";

/** Reconfigure ReferenceInput to filter by the displayed repr field. */
const ReferenceInput = (props) => {
    const ref = props["reference"];
    const repr = STATE["resources"][ref]["repr"];
    return (
        <_ReferenceInput sort={{"field": repr, "order": "ASC"}} {...props}>
            <AutocompleteInput filterToQuery={s => ({[repr]: s})} />
        </_ReferenceInput>
    );
};


const _body = document.querySelector("body");
const STATE = JSON.parse(_body.dataset.state);
// Create a mapping of components, so we can reference them by name later.
const COMPONENTS = {BooleanField, DateField, NumberField, ReferenceField, ReferenceManyField, TextField,
                    BooleanInput, DateInput, NumberInput, ReferenceInput, TextInput};

/** Make an authenticated API request and return the response object. */
function apiRequest(url, options) {
    const headers = new Headers({
        Accept: "application/json",
        Authorization: localStorage.getItem("identity")
    });
    return fetch(url, Object.assign({"headers": headers}, options)).then((resp) => {
        if (resp.status < 200 || resp.status >= 300) {
            return resp.text().then(text => {
                throw new HttpError(text, resp.status, text);
            });
        }
        return resp;
    });
}

/** Make a dataProvider request to the given resource's endpoint and return the JSON result. */
function dataRequest(resource, endpoint, params) {
    for (const [k, v] of Object.entries(params)) {
        if (v === undefined)
            delete params[k];
        if (typeof v === "object" && v !== null)
            params[k] = JSON.stringify(v);
    }
    const query = new URLSearchParams(params).toString();

    const [method, url] = STATE["resources"][resource]["urls"][endpoint];
    return apiRequest(`${url}?${query}`, {"method": method}).then((resp) => resp.json());
}


const dataProvider = {
    create: (resource, params) => dataRequest(resource, "create", params),
    delete: (resource, params) => dataRequest(resource, "delete", params),
    deleteMany: (resource, params) => dataRequest(resource, "delete_many", params),
    getList: (resource, params) => dataRequest(resource, "get_list", params),
    getMany: (resource, params) => dataRequest(resource, "get_many", params),
    getManyReference: (resource, params) => {
        params["filter"][params["target"]] = params["id"];
        return dataRequest(resource, "get_list", params);
    },
    getOne: (resource, params) => dataRequest(resource, "get_one", params),
    update: (resource, params) => dataRequest(resource, "update", params),
    updateMany: (resource, params) => dataRequest(resource, "update_many", params)
}

const authProvider = {
    login: ({username, password}) => {
        const body = JSON.stringify({username, password});
        return apiRequest(STATE["urls"]["token"], {"method": "POST", "body": body}, true).then((resp) => {
            localStorage.setItem("identity", resp.headers.get("X-Token"));
        });
    },
    logout: () => {
        return apiRequest(STATE["urls"]["logout"], {"method": "DELETE"}, true).then((resp) => {
            localStorage.removeItem("identity");
        });
    },
    checkAuth: () => {
        return localStorage.getItem("identity") ? Promise.resolve() : Promise.reject();
    },
    checkError: (error) => {
        return error.status === 401 ?  Promise.reject() : Promise.resolve();
    },
    getIdentity: () => {
        return Promise.resolve(JSON.parse(localStorage.getItem("identity")));
    },
    getPermissions: () => {
        const identity = JSON.parse(localStorage.getItem("identity"));
        return Promise.resolve(identity ? identity["permissions"] : []);
    },
};


function createFields(resource, name, permissions) {
    let components = [];
    for (const [field, state] of Object.entries(resource["fields"])) {
        if (!hasPermission(`${name}.${field}.view`, permissions))
            continue;

        const C = COMPONENTS[state["type"]];
        if (C === undefined)
            throw Error(`Unknown component '${state["type"]}'`);

        let c;
        if (state["props"]["children"]) {
            let child_fields = createFields({"fields": state["props"]["children"],
                                             "display": Object.keys(state["props"]["children"])},
                                            name, permissions);
            delete state["props"]["children"];
            c = <C source={field} {...state["props"]}><Datagrid>{child_fields}</Datagrid></C>;
        } else {
            c = <C source={field} {...state["props"]} />;
        }
        // Show icon if user doesn't have permission to view this field (based on filters).
        components.push(<WithRecord label={state["props"]["label"] || field} render={
            (record) => hasPermission(`${name}.${field}.view`, permissions, record) ? c : <VisibilityOffIcon />
        } />);
    }
    return components;
}

function createInputs(resource, name, perm_type, permissions) {
    let components = [];
    const resource_filters = getFilters(name, perm_type, permissions);
    for (const [field, state] of Object.entries(resource["inputs"])) {
        if ((perm_type === "add" && !state["show_create"])
            || !hasPermission(`${name}.${field}.${perm_type}`, permissions))
            continue;

        const fvalues = resource_filters[field];
        if (fvalues !== undefined) {
            // If there are filters for the resource-level permission which depend on
            // this field, then restrict the input options to the allowed values.
            const disabled = fvalues.length <= 1;
            const nullable = fvalues.indexOf(null);
            if (nullable > -1)
                fvalues.splice(nullable, 1);
            let choices = [];
            for (let v of fvalues)
                choices.push({"id": v, "name": v});
            components.push(
                <SelectInput source={field} choices={choices} defaultValue={nullable < 0 && fvalues[0]}
                    validate={nullable < 0 && required()} disabled={disabled} />);
        } else {
            const C = COMPONENTS[state["type"]];
            if (C === undefined)
                throw Error(`Unknown component '${state["type"]}'`);
            const c = <C source={field} {...state["props"]} />;
            if (perm_type === "edit")
                // Don't render if filters disallow editing this field.
                components.push(<WithRecord render={
                    (record) => hasPermission(`${name}.${field}.${perm_type}`, permissions, record) && c
                } />);
            else
                components.push(c);
        }
    }
    return components;
}

function createBulkUpdates(resource, name, permissions) {
    let buttons = [];
    for (const [label, data] of Object.entries(resource["bulk_update"])) {
        let allowed = true;
        for (const k of Object.keys(data)) {
            if (!hasPermission(`${name}.${k}.edit`, permissions)) {
                allowed = false;
                break;
            }
        }
        if (allowed)
            buttons.push(<BulkUpdateButton label={label} data={data} />);
    }
    return buttons;
}

const AiohttpList = (resource, name, permissions) => {
    const ListActions = () => (
        <TopToolbar>
            <SelectColumnsButton />
            <FilterButton />
            {hasPermission(`${name}.add`, permissions) && <CreateButton />}
            <ExportButton />
        </TopToolbar>
    );
    const BulkActionButtons = () => (
        <>
            {hasPermission(`${name}.edit`, permissions) && createBulkUpdates(resource, name, permissions)}
            <BulkExportButton />
            {hasPermission(`${name}.delete`, permissions) && <BulkDeleteButton />}
        </>
    );

    console.log(resource["list_omit"]);
    return (
        <List actions={<ListActions />} filters={createInputs(resource, name, "view", permissions)}>
            <DatagridConfigurable omit={resource["list_omit"]} rowClick="show" bulkActionButtons={<BulkActionButtons />}>
                {createFields(resource, name, permissions)}
                <WithRecord render={(record) => hasPermission(`${name}.edit`, permissions, record) && <EditButton />} />
            </DatagridConfigurable>
        </List>
    );
}

const AiohttpShow = (resource, name, permissions) => (
    <Show>
        <SimpleShowLayout>
            {createFields(resource, name, permissions)}
        </SimpleShowLayout>
    </Show>
);

const AiohttpEdit = (resource, name, permissions) => (
    <Edit>
        <SimpleForm>
            {createInputs(resource, name, "edit", permissions)}
        </SimpleForm>
    </Edit>
);

const AiohttpCreate = (resource, name, permissions) => (
    <Create>
        <SimpleForm>
            {createInputs(resource, name, "add", permissions)}
        </SimpleForm>
    </Create>
);

/** Return any filters for a given permission. */
function getFilters(name, perm_type, permissions) {
    let filters = permissions[`admin.${name}.${perm_type}`];
    if (filters !== undefined)
        return filters;
    filters = permissions[`admin.${name}.*`];
    return filters || {};
}

/** Return true if a user has the given permission.

A record can be passed as the context parameter in order to check permission filters
against the current record.
*/
function hasPermission(p, permissions, context=null) {
    const parts = ["admin", ...p.split(".")];
    const type = parts.pop();

    // Negative permissions.
    for (let i=parts.length; i > 0; --i) {
        for (let t of [type, "*"]) {
            let perm = [...parts.slice(0, i), t].join(".");
            if (permissions["~" + perm] !== undefined)
                return false;
        }
    }

    // Positive permissions.
    for (let i=parts.length; i > 0; --i) {
        for (let t of [type, "*"]) {
            let perm = [...parts.slice(0, i), t].join(".");
            if (permissions[perm] !== undefined) {
                if (!context)
                    return true;

                let filters = permissions[perm];
                for (let attr of Object.keys(filters)) {
                    if (!filters[attr].includes(context[attr]))
                        return false;
                }
                return true;
            }
        }
    }
    return false;
}

const AiohttpIcon = (path) => {
    return (
        <img src={path} alt="" class="MuiSvgIcon-root MuiSvgIcon-fontSizeMedium css-vubbuv" aria-hidden="true" />
    );
};

function createResources(resources, permissions) {
    let components = [];
    for (const [name, r] of Object.entries(resources)) {
        components.push(<Resource
            name={name}
            create={hasPermission(`${name}.add`, permissions) ? AiohttpCreate(r, name, permissions) : null}
            edit={hasPermission(`${name}.edit`, permissions) ? AiohttpEdit(r, name, permissions) : null}
            list={hasPermission(`${name}.view`, permissions) ? AiohttpList(r, name, permissions) : null}
            show={hasPermission(`${name}.view`, permissions) ? AiohttpShow(r, name, permissions) : null}
            options={{ label: r["label"] }}
            recordRepresentation={r["repr"]}
            icon={r["icon"] ? () => AiohttpIcon(r["icon"]) : null}
        />);
    }
    return components;
}

const AiohttpAppBar = () => (
    <AppBar>
        <TitlePortal />
        <InspectorButton />
    </AppBar>
);

const App = () => (
    <Admin dataProvider={dataProvider} authProvider={authProvider} title={STATE["view"]["name"]}
           layout={(props) => <Layout {...props} appBar={AiohttpAppBar} />} disableTelemetry requireAuth>
        {permissions => createResources(STATE["resources"], permissions)}
    </Admin>
);

export default App;
