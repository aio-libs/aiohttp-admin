import {useState} from "react";
import {
    Admin, AppBar, AutocompleteInput,
    BooleanField, BooleanInput, BulkDeleteButton, Button, BulkExportButton, BulkUpdateButton,
    CloneButton, Create, CreateButton,
    Datagrid, DatagridConfigurable, DateField, DateInput, DateTimeInput, DeleteButton,
    Edit, EditButton, ExportButton,
    FilterButton, HttpError, InspectorButton,
    Layout, List, ListButton,
    NullableBooleanInput, NumberInput, NumberField,
    ReferenceField, ReferenceInput, ReferenceManyField, ReferenceOneField, Resource,
    SaveButton, SelectColumnsButton, SelectField, SelectInput, Show, ShowButton,
    SimpleForm, SimpleShowLayout,
    TextField, TextInput, TimeInput, TitlePortal, Toolbar, TopToolbar,
    WithRecord,
    downloadCSV, email, maxLength, maxValue, minLength, minValue, regex, required,
    useCreate, useCreatePath, useDataProvider, useDelete, useDeleteMany,
    useGetList, useGetMany, useGetOne, useGetRecordId,
    useInfiniteGetList, useInput, useNotify,
    useRecordContext, useRedirect, useRefresh, useResourceContext, useUnselect,
    useUnselectAll, useUpdate, useUpdateMany,
} from "react-admin";
import {useFormContext} from "react-hook-form";
import jsonExport from "jsonexport/dist";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";

window.ReactAdmin = {
    Admin, AppBar, AutocompleteInput,
    BooleanField, BooleanInput, BulkDeleteButton, Button, BulkExportButton, BulkUpdateButton,
    CloneButton, Create, CreateButton,
    Datagrid, DatagridConfigurable, DateField, DateInput, DateTimeInput, DeleteButton,
    Edit, EditButton, ExportButton,
    FilterButton, HttpError, InspectorButton,
    Layout, List, ListButton,
    NullableBooleanInput, NumberInput, NumberField,
    ReferenceField, ReferenceInput, ReferenceManyField, ReferenceOneField, Resource,
    SaveButton, SelectColumnsButton, SelectField, SelectInput, Show, ShowButton,
    SimpleForm, SimpleShowLayout,
    TextField, TextInput, TimeInput, TitlePortal, Toolbar, TopToolbar,
    WithRecord,
    downloadCSV, email, maxLength, maxValue, minLength, minValue, regex, required,
    useCreate, useCreatePath, useDelete, useDataProvider, useDeleteMany,
    useGetList, useGetMany, useGetOne, useGetRecordId,
    useInfiniteGetList, useInput, useNotify,
    useRecordContext, useRedirect, useRefresh, useResourceContext, useUnselect,
    useUnselectAll, useUpdate, useUpdateMany,
};

let STATE;

// Hacked TimeField/TimeInput to actually work with times.
// TODO: Replace once new components are introduced using Temporal API.

const _TimeField = (props) => (
    <WithRecord {...props} render={
        (record) => <DateField {...props} showDate={false} showTime={true}
                     record={{...record, [props["source"]]: record[props["source"]] === null ? null : "2020-01-01T" + record[props["source"]]}} />
    } />
);

const _TimeInput = (props) => (<TimeInput format={(v) => v} parse={(v) => v} {...props} />);

/** Reconfigure ReferenceInput to filter by the displayed repr field. */
const _ReferenceInput = (props) => {
    const {referenceKeys, ...innerProps} = props;
    const {setValue} = useFormContext();
    const change = (value, record) => {
        for (let [this_k, foreign_k] of referenceKeys)
            setValue(`data.${this_k}`, record ? record["data"][foreign_k] : null);
    };

    const ref = props["reference"];
    const repr = STATE["resources"][ref]["repr"].replace(/^data\./, "");
    return (
        <ReferenceInput sort={{"field": repr, "order": "ASC"}} {...innerProps}>
            <AutocompleteInput filterToQuery={s => ({[repr]: s})} label={props["label"]} onChange={change} validate={props["validate"]} />
        </ReferenceInput>
    );
};

/** Display a single record in a Datagrid-like view (e.g. for ReferenceField). */
const DatagridSingle = (props) => (
    <WithRecord {...props} render={
        (record) => <Datagrid {...props} data={[record]} bulkActionButtons={false}
                     hover={false} rowClick={false} setSort={null}
                     sort={{field: "id", order: "DESC"}} />
    } />
);

const exportRecords = (records) => records.map((record) => record.data);

// Create a mapping of components, so we can reference them by name later.
const COMPONENTS = {
    Datagrid, DatagridSingle,

    BulkDeleteButton, BulkExportButton, BulkUpdateButton, CloneButton, CreateButton,
    ExportButton, FilterButton, ListButton, ShowButton,

    BooleanField, DateField, NumberField, ReferenceField, ReferenceManyField,
    ReferenceOneField, SelectField, TextField, TimeField: _TimeField,

    BooleanInput, DateInput, DateTimeInput, NullableBooleanInput, NumberInput,
    ReferenceInput: _ReferenceInput, SelectInput, TextInput, TimeInput: _TimeInput
};
const FUNCTIONS = {exportRecords, email, maxLength, maxValue, minLength, minValue, regex, required};

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
        else if (typeof v === "object" && v !== null)
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
        // filter object is reused across requests, so clone it before modifying.
        params["filter"] = {...params["filter"], [params["target"]]: params["id"]};
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

function evaluate(obj) {
    if (obj === null || obj === undefined)
        return obj;
    if (Array.isArray(obj))
        return obj.map(evaluate);
    if (obj["__type__"] === "component") {
        const C = COMPONENTS[obj["type"]];
        if (C === undefined)
            throw Error(`Unknown component '${obj["type"]}'`);

        let {children, ...props} = obj["props"];
        props = Object.fromEntries(Object.entries(props).map(([k, v]) => [k, evaluate(v)]));
        if (!props["key"])
            props["key"] = props["source"] || obj["type"];
        if (children)
            return <C {...props}>{evaluate(children)}</C>;
        return <C {...props} />;
    }
    if (obj["__type__"] === "function") {
        const f = FUNCTIONS[obj["name"]];
        if (f === undefined)
            throw Error(`Unknown function '${obj["name"]}'`);
        if (obj["args"] === null)
            return f;
        return f(...evaluate(obj["args"]));
    }
    if (obj["__type__"] === "regexp")
        return new RegExp(obj["value"]);
    return obj;
}


function createFields(fields, name, permissions) {
    let components = [];
    for (const state of Object.values(fields)) {
        const field = state["props"]["source"].replace(/^data\./, "");
        if (!hasPermission(`${name}.${field}.view`, permissions))
            continue;

        const c = evaluate(state);
        const withRecordPropNames = ["label", "sortable", "sortBy", "sortByOrder", "source"];
        const withRecordProps = Object.fromEntries(withRecordPropNames.map((k) => [k, c.props[k]]));
        // Show icon if user doesn't have permission to view this field (based on filters).
        components.push(<WithRecord key={c.key} {...withRecordProps} render={
            (record) => hasPermission(`${name}.${field}.view`, permissions, record) ? c : <VisibilityOffIcon />
        } />);
    }
    return components;
}

function createInputs(resource, name, perm_type, permissions) {
    let components = [];
    const resource_filters = getFilters(name, perm_type, permissions);
    for (let state of Object.values(resource["inputs"])) {
        const field = state["props"]["source"].replace(/^data\./, "");
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
                <SelectInput label={state["props"]["label"]} source={state["props"]["source"]} key={state["props"]["key"]} choices={choices} defaultValue={nullable < 0 && fvalues[0]}
                    validate={nullable < 0 && required()} disabled={disabled} />);
        } else {
            if (perm_type === "view") {
                state = structuredClone(state);
                delete state["props"]["validate"];
            }
            const c = evaluate(state);
            if (perm_type === "edit")
                // Don't render if filters disallow editing this field.
                components.push(<WithRecord label={c.props.label} source={c.props.source} key={c.key} render={
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
            buttons.push(<BulkUpdateButton mutationMode="pessimistic" key={label} label={label} data={data} />);
    }
    return buttons;
}

const AiohttpList = (resource, name, permissions) => {
    const exporter = (records) => {
        jsonExport(exportRecords(records), (err, csv) => downloadCSV(csv, name));
    };
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
            {hasPermission(`${name}.delete`, permissions) && <BulkDeleteButton mutationMode="pessimistic" />}
        </>
    );
    const filters = createInputs(resource, name, "view", permissions);
    // Remove inputs with duplicate sources.
    const filterSources = filters.map(c => c["props"]["source"]);

    return (
        <List actions={<ListActions />} exporter={exporter} filters={filters.filter((v, i) => filterSources.indexOf(v) === i)}>
            <DatagridConfigurable omit={resource["list_omit"]} rowClick="show" bulkActionButtons={<BulkActionButtons />}>
                {createFields(resource["fields"], name, permissions)}
                <WithRecord label="[Edit]" render={(record) => hasPermission(`${name}.edit`, permissions, record) && <EditButton />} />
            </DatagridConfigurable>
        </List>
    );
}

const AiohttpShow = (resource, name, permissions) => {
    const ShowActions = () => (
        <TopToolbar>
            {resource["show_actions"].map(evaluate)}
            <WithRecord render={(record) => hasPermission(`${name}.edit`, permissions, record) && <EditButton />} />
        </TopToolbar>
    );

    return (
        <Show actions={<ShowActions />}>
            <SimpleShowLayout>
                {createFields(resource["fields"], name, permissions)}
            </SimpleShowLayout>
        </Show>
    );
}

const AiohttpEdit = (resource, name, permissions) => {
    const EditActions = () => (
        <TopToolbar>
            <CloneButton />
            <ShowButton />
            <ListButton />
        </TopToolbar>
    );

    const AiohttpEditToolbar = props => (
        <Toolbar {...props} sx={{ display: "flex", justifyContent: "space-between" }}>
            <SaveButton />
            <WithRecord render={
                (record) => hasPermission(`${name}.delete`, permissions, record) && <DeleteButton />
            } />
        </Toolbar>
    );

    return(
        <Edit actions={<EditActions />} mutationMode="pessimistic">
            <SimpleForm toolbar={<AiohttpEditToolbar />} sanitizeEmptyValues warnWhenUnsavedChanges>
                {createInputs(resource, name, "edit", permissions)}
            </SimpleForm>
        </Edit>
    );
}

const AiohttpCreate = (resource, name, permissions) => (
    <Create redirect="show">
        <SimpleForm sanitizeEmptyValues warnWhenUnsavedChanges>
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
                    if (!filters[attr].includes(context["data"][attr]))
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

const App = (props) => {
    const {aiohttpState, ...adminProps} = props;
    STATE = aiohttpState;
    const [loaded, setLoaded] = useState(STATE["js_module"] === null);
    if (!loaded) {
        import(/* webpackIgnore: true */ STATE["js_module"]).then((mod) => {
            Object.assign(COMPONENTS, mod.components);
            Object.assign(FUNCTIONS, mod.functions);
            setLoaded(true);
        });
        return <progress></progress>;
    }

    return (
        <Admin {...adminProps} dataProvider={dataProvider} authProvider={authProvider} title={STATE["view"]["name"]}
               layout={(props) => <Layout {...props} appBar={AiohttpAppBar} />} disableTelemetry requireAuth>
            {permissions => createResources(STATE["resources"], permissions)}
        </Admin>
    );
};

export {App};
