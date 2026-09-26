import { expect, test, type Page } from "@playwright/test";

async function bootstrap(page: Page) {
  await page.goto("/");
  await expect(page.getByText("إعداد الشركة لأول مرة")).toBeVisible();

  await page.getByLabel("اسم الشركة").fill("NEXVARY Test Realty");
  await page.getByLabel("معرّف الشركة").fill("nexvary-test");
  await page.getByLabel("الاسم التجاري").fill("NEXVARY Realty");
  await page.getByLabel("اسم المالك").fill("Release Owner");
  await page.getByLabel("البريد الإلكتروني").fill("owner@nexvary.test");
  await page.getByLabel("كلمة المرور").fill("ReleaseGate123!");
  await page.getByRole("button", { name: "إنشاء الشركة والدخول" }).click();

  await expect(page.getByText("مركز قيادة المبيعات")).toBeVisible();
}

test("desktop first-run, navigation, lead flow and back button", async ({ page, isMobile }) => {
  if (isMobile) test.skip();

  await bootstrap(page);

  await page.getByRole("button", { name: "إضافة عميل" }).click();
  await page.locator('input[name="name"]').last().fill("عميل اختبار");
  await page.locator('input[name="phone"]').last().fill("01000000000");
  await page.locator('input[name="city"]').last().fill("New Cairo");
  await page.locator('input[name="budget"]').last().fill("5000000");
  await page.locator('input[name="bedrooms"]').last().fill("3");
  await page.getByRole("button", { name: "حفظ العميل" }).click();

  await expect(page.getByText("عميل اختبار")).toBeVisible();

  await page.getByRole("button", { name: "إدارة المخزون" }).click();
  await expect(page.getByText("إدارة المشروعات والوحدات")).toBeVisible();

  const projectForm = page.locator("form").filter({ hasText: "مشروع جديد" });
  await projectForm.locator('input[name="name"]').fill("بوابة القاهرة");
  await projectForm.locator('input[name="city"]').fill("New Cairo");
  await projectForm.getByRole("button", { name: "إضافة المشروع" }).click();
  await expect(page.locator('select[name="project_id"]').first()).toContainText("بوابة القاهرة");

  await page.getByRole("button", { name: "رجوع" }).click();
  await expect(page.getByText("مركز قيادة المبيعات")).toBeVisible();

  await page.getByTitle("Language").click();
  await expect(page.getByText("Sales Command Center")).toBeVisible();
});

test("mobile layout exposes navigation and does not overflow core controls", async ({ page, isMobile }) => {
  if (!isMobile) test.skip();

  await page.goto("/");
  await expect(page.locator(".loginCard")).toBeVisible();

  const viewport = page.viewportSize();
  expect(viewport).not.toBeNull();
  const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
  expect(bodyWidth).toBeLessThanOrEqual((viewport?.width || 412) + 2);

  await expect(page.getByRole("button", { name: /EN|AR/ })).toBeVisible();
});
