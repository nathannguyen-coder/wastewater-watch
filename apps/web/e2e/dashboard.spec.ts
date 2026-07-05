import { expect, test } from "@playwright/test"

test("analyst can review a real SRA signal and inspect a clear site", async ({ page }) => {
  await page.goto("/")

  await expect(page.getByRole("heading", { name: "Point Loma WTP", level: 1 })).toBeVisible()
  await expect(page.getByRole("link", { name: "W Wastewater Watch" })).toBeVisible()
  await expect(page.getByLabel("Totals across all monitoring locations")).toContainText(
    "Locations3Samples analyzed31Flagged samples8QC-held samples0",
  )
  await expect(page.getByText("NCBI SRA · PRJNA729801")).toBeVisible()
  await expect(page.getByRole("heading", { name: "Community shift at Point Loma WTP" })).toBeVisible()
  await expect(page.getByText(/not evidence of an outbreak/i)).toBeVisible()
  await expect(page.getByRole("link", { name: /SRR14530864/ })).toHaveAttribute(
    "href",
    "https://www.ncbi.nlm.nih.gov/sra/SRR14530864",
  )
  await expect(page.getByText("NCBI STAT 2.1.0")).toBeVisible()

  await page.getByRole("button", { name: /South Bay WRP/ }).click()
  await expect(page.getByRole("heading", { name: "South Bay WRP", level: 1 })).toBeVisible()
  await expect(page.getByRole("heading", { name: "No alert for this sample." })).toBeVisible()
})

test("mobile layout keeps every site and the selected sample accessible", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto("/")

  await expect(page.getByRole("button", { name: /Point Loma WTP/ })).toBeVisible()
  await expect(page.getByRole("button", { name: /South Bay WRP/ })).toBeVisible()
  await expect(page.getByRole("button", { name: /San Jose Creek WRP/ })).toBeVisible()
  await expect(page.getByRole("heading", { name: "Community shift at Point Loma WTP" })).toBeVisible()
  await expect(page.locator("body")).toHaveJSProperty("scrollWidth", 390)
})
