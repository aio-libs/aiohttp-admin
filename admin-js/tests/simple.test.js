import {within} from "@testing-library/dom";
import {screen, waitFor} from "@testing-library/react";
import userEvent from "@testing-library/user-event";

global.pythonProcessPath = "examples/simple.py";


test("login works", async () => {
    await userEvent.type(await screen.findByLabelText(/Username/), "admin");
    await userEvent.type(screen.getByLabelText(/Password/), "admin");
    await userEvent.click(screen.getByText("Sign in"));

    expect(await screen.findByText("Admin user")).toBeInTheDocument();
});

test("data is displayed", async () => {
    const table = await screen.findByRole("table");
    const headers = within(table).getAllByRole("columnheader");
    expect(headers.slice(1, -1).map((e) => e.textContent)).toEqual(["Id", "Num", "Optional num", "Value"]);

    const rows = within(table).getAllByRole("row");
    const firstCells = within(rows[1]).getAllByRole("cell").slice(1, -1);
    expect(firstCells.map((e) => e.textContent)).toEqual(["1", "5", "", "first"]);
    const secondCells = within(rows[2]).getAllByRole("cell").slice(1, -1);
    expect(secondCells.map((e) => e.textContent)).toEqual(["2", "82", "12", "with child"]);
});

test("parents are displayed", async () => {
    userEvent.click(await screen.findByRole("button", {"name": "Open menu"}));
    userEvent.click(await screen.findByText("Parents"));

    await waitFor(() => screen.getByText("USD"));
    const table = screen.getByRole("table");
    const headers = within(table).getAllByRole("columnheader");
    expect(headers.slice(1, -1).map((e) => e.textContent)).toEqual(["Id", "Date", "Currency"]);

    const rows = within(table).getAllByRole("row");
    const firstCells = within(rows[1]).getAllByRole("cell").slice(1, -1);
    expect(firstCells.map((e) => e.textContent)).toEqual(["2", "2/13/2023, 7:04:00 PM", "USD"]);
    expect(within(firstCells[0]).getByRole("link")).toBeInTheDocument();
});
