import {within} from "@testing-library/dom";
import {screen, waitFor} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {downloadCSV as mockDownloadCSV} from "react-admin";

global.pythonProcessPath = "examples/simple.py";


test("login works", async () => {
    await userEvent.click(screen.getByRole("button", {"name": "Profile"}));
    await userEvent.click(await screen.findByRole("menuitem", {"name": "Logout"}));

    await userEvent.type(await screen.findByLabelText(/Username/), "admin");
    await userEvent.type(screen.getByLabelText(/Password/), "admin");
    await userEvent.click(screen.getByRole("button", {"name": "Sign in"}));

    expect(await screen.findByText("Admin user")).toBeInTheDocument();
});

test("data is displayed", async () => {
    const table = await screen.findByRole("table");
    const headers = within(table).getAllByRole("columnheader");
    expect(headers.slice(1, -1).map((e) => e.textContent)).toEqual(["Id", "Num", "Optional Num", "Value"]);

    const rows = within(table).getAllByRole("row");
    const firstCells = within(rows[1]).getAllByRole("cell").slice(1, -1);
    expect(firstCells.map((e) => e.textContent)).toEqual(["1", "5", "", "first"]);
    const secondCells = within(rows[2]).getAllByRole("cell").slice(1, -1);
    expect(secondCells.map((e) => e.textContent)).toEqual(["2", "82", "12", "with child"]);
});

test("parents are displayed", async () => {
    await userEvent.click(await screen.findByRole("button", {"name": "Open menu"}));
    await userEvent.click(await screen.findByText("Parents"));

    await waitFor(() => screen.getByText("USD"));
    const table = screen.getByRole("table");
    const headers = within(table).getAllByRole("columnheader");
    expect(headers.slice(1, -1).map((e) => e.textContent)).toEqual(["Id", "Date", "Currency"]);

    const rows = within(table).getAllByRole("row");
    const firstCells = within(rows[1]).getAllByRole("cell").slice(1, -1);
    expect(firstCells.map((e) => e.textContent)).toEqual(["with child", "2/13/2023, 7:04:00 PM", "USD"]);
    expect(within(firstCells[0]).getByRole("link")).toBeInTheDocument();
});

test("filter labels are correct", async () => {
    const main = await screen.findByRole("main");
    const quickSearch = main.querySelector("form");
    const labels = quickSearch.querySelectorAll("label");
    expect(Array.from(labels).map((e) => e.textContent)).toEqual(["Id", "Num", "Optional Num", "Value"]);
});

test("parent filter labels are correct", async () => {
    await userEvent.click(await screen.findByRole("button", {"name": "Open menu"}));
    await userEvent.click(await screen.findByText("Parents"));

    await waitFor(() => screen.getByText("USD"));
    const main = await screen.findByRole("main");
    const quickSearch = main.querySelector("form");
    const labels = quickSearch.querySelectorAll("label");
    expect(Array.from(labels).map((e) => e.textContent)).toEqual(["Id", "Date", "Currency"]);
});

test("filters work", async () => {
    const main = await screen.findByRole("main");
    const quickSearch = main.querySelector("form");
    const table = await within(main).findByRole("table");
    let rows = within(table).getAllByRole("row");
    expect(rows.length).toBeGreaterThan(2);
    const sb = within(quickSearch).getByRole("spinbutton", {"name": "Id"});
    await userEvent.type(sb, "1");

    /*await waitFor(() => within(main).getByRole("button", {"name": "Add filter"}));
    await sleep(0.5);
    rows = within(table).getAllByRole("row");
    expect(rows.length).toBe(2);
    expect(within(rows[1]).getAllByRole("cell")[1]).toHaveTextContent("1");*/
});

test("enum filter works", async () => {
    await userEvent.click(await screen.findByRole("button", {"name": "Open menu"}));
    await userEvent.click(await screen.findByText("Parents"));
    await waitFor(() => screen.getByText("USD"));

    const main = screen.getByRole("main");
    const quickSearch = main.querySelector("form");
    const table = within(main).getByRole("table");
    const currencySelect = within(quickSearch).getByRole("combobox", {"name": "Currency"});
    expect(within(table).getAllByRole("row").length).toBe(2);
    const record = within(table).getAllByRole("row")[1];
    await userEvent.click(currencySelect);
    await userEvent.click(await screen.findByRole("option", {"name": "GBP"}));

    expect(await within(main).findByText("No results found")).toBeInTheDocument();
    expect(within(main).queryByRole("table")).not.toBeInTheDocument();

    await userEvent.click(currencySelect);
    await userEvent.click(await screen.findByRole("option", {"name": "USD"}));

    await waitFor(() => expect(within(main).getByRole("table")).toBeInTheDocument());
    const rows = within(within(main).getByRole("table")).getAllByRole("row");
    expect(currencySelect).toHaveTextContent("USD");
    expect(rows.length).toBe(2);
    expect(within(rows[1]).getByText("USD")).toBeInTheDocument();
});

test("edit form", async () => {
    await userEvent.click((await screen.findAllByLabelText("Edit"))[0]);
    await waitFor(() => screen.getByRole("link", {"name": "List"}));

    const main = screen.getByRole("main");
    const edit = main.querySelector("form");
    const id = within(edit).getByLabelText("Id *");
    //expect(id).toBeRequired();
    expect(id).toHaveValue(1);
    const num = within(edit).getByLabelText("Num *");
    //expect(num).toBeRequired();
    expect(num).toHaveValue(5);
    const opt = within(edit).getByLabelText("Optional Num");
    expect(opt).not.toBeRequired();
    expect(opt).toHaveValue(null);
    const value = within(edit).getByLabelText("Value *");
    //expect(value).toBeRequired();
    expect(value).toHaveValue("first");
});

test("reference input label", async () => {
    await userEvent.click(await screen.findByRole("button", {"name": "Open menu"}));
    await userEvent.click(await screen.findByText("Parents"));

    await waitFor(() => screen.getByText("USD"));
    await userEvent.click(screen.getAllByLabelText("Edit")[0]);
    await waitFor(() => screen.getByRole("link", {"name": "List"}));

    const main = screen.getByRole("main");
    const edit = main.querySelector("form");
    expect(within(edit).getByLabelText("Id *")).toHaveValue("with child");
});

test("reference input filter", async () => {
    await userEvent.click(await screen.findByRole("button", {"name": "Open menu"}));
    await userEvent.click(await screen.findByText("Parents"));
    await waitFor(() => screen.getByText("USD"));

    const main = screen.getByRole("main");
    const quickSearch = main.querySelector("form");
    const input = within(quickSearch).getByRole("combobox", {"name": "Id"});
    const table = within(main).getByRole("table");
    expect(within(table).getAllByRole("row").length).toBe(2);
    await userEvent.click(within(input.parentElement).getByRole("button", {"name": "Open"}));
    const resultsInitial = await screen.findByRole("listbox", {"name": "Id"});
    const optionsInitial = within(resultsInitial).getAllByRole("option");
    expect(optionsInitial.map(e => e.textContent)).toEqual(["first", "with child"]);

    await userEvent.click(within(resultsInitial).getByRole("option", {"name": "first"}));
    await waitFor(() => expect(screen.queryByText("USD")).not.toBeInTheDocument());
    expect(await within(main).findByText("No results found")).toBeInTheDocument();

    await userEvent.type(input, "w");
    const resultsFiltered = await screen.findByRole("listbox", {"name": "Id"});
    const optionsFiltered = within(resultsFiltered).getAllByRole("option");
    expect(optionsFiltered.map(e => e.textContent)).toEqual(["with child"]);

    await userEvent.click(within(resultsFiltered).getByRole("option", {"name": "with child"}));
    await waitFor(() => expect(screen.queryByText("USD")).toBeInTheDocument());
    expect(within(table).getAllByRole("row").length).toBe(2);
});

test("export works", async () => {
    await userEvent.click(await screen.findByRole("button", {"name": "Export"}));
    await waitFor(() => expect(mockDownloadCSV).toHaveBeenCalled());

    const csv = "id,num,optional_num,value\n1,5,,first\n2,82,12,with child";
    expect(mockDownloadCSV).toHaveBeenCalledWith(csv, "simple");
});

test("create form works", async () => {
    await userEvent.click(await screen.findByLabelText("Create"));
    await waitFor(() => screen.getByRole("heading", {"name": "Create Simple"}));

    await userEvent.type(screen.getByLabelText("Num *"), "12");
    await userEvent.type(screen.getByLabelText("Value *"), "Foo");
    await userEvent.click(screen.getByRole("button", {"name": "Save"}));

    const main = await screen.findByRole("main");
    expect(await within(main).findByText("3")).toBeInTheDocument();
    expect(within(main).getByText("12")).toBeInTheDocument();
    expect(within(main).getByText("Foo")).toBeInTheDocument();
});

test("edit submit", async () => {
    await userEvent.click((await screen.findAllByLabelText("Edit"))[0]);
    await waitFor(() => screen.getByRole("link", {"name": "List"}));
    const form = screen.getByRole("main").querySelector("form");
    expect(within(form).getByLabelText("Id *")).toHaveValue(1);

    await userEvent.type(within(form).getByLabelText("Id *"), "3");
    await userEvent.type(within(form).getByLabelText("Num *"), "7");
    await userEvent.click(within(form).getByRole("button", {"name": "Save"}));

    const table = await screen.findByRole("table");
    await sleep(0.2);
    const rows = within(table).getAllByRole("row");
    const cells = within(rows.at(-1)).getAllByRole("cell").slice(1, -1);
    expect(cells.map((e) => e.textContent)).toEqual(["13", "57", "", "first"]);

    expect(within(table).queryByText("1")).not.toBeInTheDocument();
});

test("reference input edit", async () => {
    await userEvent.click(await screen.findByRole("button", {"name": "Open menu"}));
    await userEvent.click(await screen.findByText("Parents"));
    await waitFor(() => screen.getByText("USD"));

    await userEvent.click(screen.getAllByLabelText("Edit")[0]);
    await waitFor(() => screen.getByRole("link", {"name": "List"}));
    const form = screen.getByRole("main").querySelector("form");
    const idInput = within(form).getByLabelText(/Id/);
    expect(idInput).toHaveValue("with child");

    await userEvent.click(within(idInput.parentElement).getByRole("button", {"name": "Open"}));
    const results = await screen.findByRole("listbox", {"name": "Id"});
    await userEvent.click(await within(results).findByRole("option", {"name": "first"}));
    expect(idInput).toHaveValue("first");
    await userEvent.click(within(form).getByRole("button", {"name": "Save"}));

    const table = await screen.findByRole("table");
    await sleep(0.2);
    const rows = within(table).getAllByRole("row");
    expect(rows.length).toEqual(2);
    const idCell = within(rows[1]).getAllByRole("cell")[1];
    expect(idCell).toHaveTextContent("first");
});
