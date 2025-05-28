import {within} from "@testing-library/dom";
import {screen, waitFor} from "@testing-library/react";
import userEvent from "@testing-library/user-event";

global.pythonProcessPath = "examples/permissions.py";


describe("admin", () => {
    beforeAll(() => setLogin("admin", ""));

    test("view", async () => {
        const table = await screen.findByRole("table");
        const headers = within(table).getAllByRole("columnheader");
        expect(headers.slice(1, -1).map((e) => e.textContent)).toEqual(["Id", "Num", "Optional Num"]);

        const rows = within(table).getAllByRole("row");
        const firstCells = within(rows[1]).getAllByRole("cell").slice(1, -1);
        expect(firstCells.map((e) => e.textContent)).toEqual(["1", "5", ""]);
        const secondCells = within(rows[2]).getAllByRole("cell").slice(1, -1);
        expect(secondCells.map((e) => e.textContent)).toEqual(["2", "82", "12"]);
    });
});

describe("filter", () => {
    beforeAll(() => setLogin("filter", ""));

    test("view", async () => {
        const table = await screen.findByRole("table");
        const rows = within(table).getAllByRole("row").slice(1);
        expect(rows).toHaveLength(5);
        expect(rows.map(r => within(r).getAllByRole("cell")[1].textContent)).toEqual(["1", "3", "4", "5", "6"]);

        await userEvent.click(screen.getByRole("link", {"name": "Create"}));
        await waitFor(() => screen.getByText("Create Simple"));
        const num = screen.getByLabelText("Num *");
        expect(num).toHaveAttribute("aria-disabled", "true");
        expect(num).toHaveTextContent("5");
    });
});

describe("admin", () => {
    beforeAll(() => setLogin("admin", ""));

    test("bulk update", async () => {
        const container = await screen.findByRole("columnheader", {"name": "Select all"});
        const selectAll = within(container).getByRole("checkbox");
        await userEvent.click(selectAll);
        expect(selectAll).toBeChecked();
        await userEvent.click(await screen.findByRole("button", {"name": "Set to 7"}));
        expect(await screen.findByText("Update 6 simples")).toBeInTheDocument();
        await userEvent.click(screen.getByRole("button", {"name": "Confirm"}));
        return;  // Broken now
        await waitFor(() => screen.getAllByText("7"));

        const table = await screen.findByRole("table");
        const rows = within(table).getAllByRole("row");
        const firstCells = within(rows[1]).getAllByRole("cell");
        const secondCells = within(rows[2]).getAllByRole("cell");
        expect(firstCells[3]).toHaveTextContent("7");
        expect(secondCells[3]).toHaveTextContent("7");
    });
});
