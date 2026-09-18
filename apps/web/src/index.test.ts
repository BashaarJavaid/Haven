import { expect, test } from "vitest";

test("workspace module imports", async () => {
  expect(Object.keys(await import("./index"))).toEqual([]);
});
