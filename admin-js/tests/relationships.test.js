import {within} from "@testing-library/dom";
import {screen, waitFor} from "@testing-library/react";
import userEvent from "@testing-library/user-event";

global.pythonProcessPath = "examples/relationships.py";


test("datagrid works", async () => {
    const table = await screen.findByRole("table");
    await userEvent.click(screen.getByRole("button", {"name": "Columns"}));
    await userEvent.click(within(screen.getByRole("presentation")).getByLabelText("Children"));
    await userEvent.keyboard("[Escape]");

    const grid = await within(table).findByRole("table");
    const childHeaders = within(grid).getAllByRole("columnheader");
    expect(childHeaders.slice(1).map((e) => e.textContent)).toEqual(["Id", "Name", "Value"]);
    const childRows = within(grid).getAllByRole("row");
    expect(childRows.length).toBe(3);
    const firstCells = within(childRows[1]).getAllByRole("cell");
    expect(firstCells.slice(1).map((e) => e.textContent)).toEqual(["2", "Child Bar", "5"]);
    const secondCells = within(childRows[2]).getAllByRole("cell");
    expect(secondCells.slice(1).map((e) => e.textContent)).toEqual(["1", "Child Foo", "1"]);

    const h = within(grid).getByRole("columnheader", {"name": "Select all"});
    const check = within(h).getByRole("checkbox");
    await userEvent.click(check);
    expect(check).toBeChecked();
    // Check page hasn't redirected to show view.
    expect(location.href).toMatch(/\/onetomany_parent$/);
});

test("onetomany child displays", async () => {
    await userEvent.click(await screen.findByRole("button", {"name": "Open menu"}));
    await userEvent.click(await screen.findByText("Onetomany children"));

    await waitFor(() => screen.getByRole("heading", {"name": "Onetomany children"}));
    await sleep(1);

    await userEvent.click(screen.getByRole("button", {"name": "Columns"}));
    // TODO: Remove when fixed: https://github.com/marmelab/react-admin/issues/9587
    await userEvent.click(within(screen.getByRole("presentation")).getByLabelText("Parent Id"));
    await userEvent.click(within(screen.getByRole("presentation")).getByLabelText("Parent"));
    await userEvent.keyboard("[Escape]");

    const table = screen.getAllByRole("table")[0];
    const headers = within(table.querySelector("thead")).getAllByRole("columnheader");
    expect(headers.slice(1, -1).map((e) => e.textContent)).toEqual(["Id", "Name", "Value", "Parent Id", "Parent"]);

    const rows = within(table).getAllByRole("row").filter((e) => e.parentElement.parentElement === table);
    const firstCells = within(rows[1]).getAllByRole("cell").filter((e) => e.parentElement === rows[1]);
    expect(firstCells.slice(1, -2).map((e) => e.textContent)).toEqual(["1", "Child Foo", "1", "Bar"]);
    const secondCells = within(rows[2]).getAllByRole("cell").filter((e) => e.parentElement === rows[2]);
    expect(secondCells.slice(1, -2).map((e) => e.textContent)).toEqual(["2", "Child Bar", "5", "Bar"]);

    const grid = within(firstCells.at(-2)).getByRole("table");
    const childHeaders = within(grid).getAllByRole("columnheader");
    expect(childHeaders.map((e) => e.textContent)).toEqual(["Name", "Value"]);
    const childRows = within(grid).getAllByRole("row");
    expect(childRows.length).toBe(2);
    const childCells = within(childRows[1]).getAllByRole("cell");
    expect(childCells.map((e) => e.textContent)).toEqual(["Bar", "2"]);
});

test("composite foreign key child displays table", async () => {
    await userEvent.click(await screen.findByRole("button", {"name": "Open menu"}));
    await userEvent.click(await screen.findByText("Composite foreign key children"));

    await waitFor(() => screen.getByRole("heading", {"name": "Composite foreign key children"}));
    await userEvent.click(screen.getByRole("button", {"name": "Columns"}));
    await userEvent.click(within(screen.getByRole("presentation")).getByLabelText("Parents"));
    await userEvent.keyboard("[Escape]");
    await sleep(0.5);
    const table = screen.getAllByRole("table")[0];
    const rows = within(table).getAllByRole("row").filter((e) => e.parentElement.parentElement === table);
    const cells = within(rows[2]).getAllByRole("cell").filter((e) => e.parentElement === rows[2]);
    expect(cells.slice(1, -2).map((e) => e.textContent)).toEqual(["0", "1", "B"]);
    expect(within(rows[1]).getAllByRole("cell").at(-2)).toHaveTextContent("No results found");

    const grid = within(cells.at(-2)).getByRole("table");
    const childHeaders = within(grid).getAllByRole("columnheader");
    expect(childHeaders.slice(1).map((e) => e.textContent)).toEqual(["Item Id", "Item Name"]);
    const childRows = within(grid).getAllByRole("row");
    expect(childRows.length).toBe(2);
    const childCells = within(childRows[1]).getAllByRole("cell");
    expect(childCells.slice(1).map((e) => e.textContent)).toEqual(["1", "Foo"]);
});

test("composite foreign key parent displays", async () => {
    await userEvent.click(await screen.findByRole("button", {"name": "Open menu"}));
    await userEvent.click(await screen.findByText("Composite foreign key parents"));

    await waitFor(() => screen.getByRole("heading", {"name": "Composite foreign key parents"}));
    await sleep(1);
    const table = screen.getAllByRole("table")[0];
    const rows = within(table).getAllByRole("row").filter((e) => e.parentElement.parentElement === table);
    const cells = within(rows[1]).getAllByRole("cell").filter((e) => e.parentElement === rows[1]);
    expect(cells.slice(1, -1).map((e) => e.textContent)).toEqual(["1", "Foo"]);
    await userEvent.click(rows[1]);

    await waitFor(() => screen.getByRole("heading", {"name": "Composite foreign key parent"}));
    const main = screen.getByRole("main");
    expect((await within(main).findAllByRole("link", {"name": "B"}))[0]).toHaveTextContent("B");

    const grid = within(main).getByRole("table");
    const headers = within(grid).getAllByRole("columnheader");
    expect(headers.map((e) => e.textContent)).toEqual(["Description"]);
    const childRows = within(grid).getAllByRole("row");
    expect(childRows.length).toBe(2);
    const childCells = within(childRows[1]).getAllByRole("cell");
    expect(childCells.map((e) => e.textContent)).toEqual(["B"]);
});

test("composite foreign key reference input updates", async () => {
    await userEvent.click(await screen.findByRole("button", {"name": "Open menu"}));
    await userEvent.click(await screen.findByText("Composite foreign key parents"));

    await waitFor(() => screen.getByRole("heading", {"name": "Composite foreign key parents"}));
    const table = screen.getAllByRole("table")[0];
    const rows = within(table).getAllByRole("row").filter((e) => e.parentElement.parentElement === table);
    await userEvent.click(within(rows[1]).getByRole("link", {"name": "Edit"}));

    await waitFor(() => screen.getByRole("heading", {"name": "Composite foreign key parent"}));
    // TODO: identifiers are screwed up for these inputs.
    const referenceInput = await screen.findByRole("combobox", {"name": "Child Id Ref Num"});
    const referenceInput2 = await screen.findByRole("combobox", {"name": ""});
    await waitFor(() => expect(referenceInput).not.toHaveValue(""));
    expect(referenceInput).toHaveValue("B");
    expect(referenceInput2).toHaveValue("B");
    await userEvent.click(within(referenceInput.parentElement).getByRole("button", {"name": "Open"}));

    const popup = await screen.findByRole("presentation");
    const options = within(popup).getAllByRole("option");
    expect(options.map(e => e.textContent)).toEqual(["A", "C"]);
    await userEvent.click(within(popup).getByRole("option", {"name": "A"}));

    expect(referenceInput).toHaveValue("A");
    expect(referenceInput2).toHaveValue("A");
    await userEvent.click(screen.getByRole("button", {"name": "Save"}));

    await waitFor(() => screen.getByRole("heading", {"name": "Composite foreign key parents"}));
    await userEvent.click(screen.getByRole("button", {"name": "Columns"}));
    await userEvent.click(within(screen.getByRole("presentation")).getByLabelText("Ref Num"));
    await userEvent.keyboard("[Escape]");
    await sleep(1);
    const table2 = screen.getAllByRole("table")[0];
    const rows2 = within(table2).getAllByRole("row").filter((e) => e.parentElement.parentElement === table2);
    const cells = within(rows2[1]).getAllByRole("cell").filter((e) => e.parentElement === rows2[1]);
    expect(cells.at(-2)).toHaveTextContent("A");
});
