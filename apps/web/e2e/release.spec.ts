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

test("platform admin creates and manages a second white-label company", async ({ page, isMobile }) => {
  if (isMobile) test.skip();

  await page.goto("/");
  await expect(page.getByRole("button", { name: "إدارة منصة NEXVARY والشركات" })).toBeVisible();
  await page.getByRole("button", { name: "إدارة منصة NEXVARY والشركات" }).click();

  await expect(page.getByText("إدارة جميع شركات العقارات")).toBeVisible();
  await page.getByLabel("البريد الإلكتروني").fill("owner@nexvary.test");
  await page.getByLabel("كلمة المرور").fill("ReleaseGate123!");
  await page.getByRole("button", { name: "دخول إدارة المنصة" }).click();

  await expect(page.getByText("إدارة شركات العقارات")).toBeVisible();
  await page.getByRole("button", { name: "شركة جديدة" }).click();

  const modal = page.locator(".platformCreateModal");
  await modal.getByLabel("اسم الشركة").fill("Atlas E2E Realty");
  await modal.getByLabel("معرّف الشركة").fill("atlas-e2e");
  await modal.getByLabel("الاسم التجاري").fill("ATLAS E2E");
  await modal.getByLabel("اسم المالك").fill("Atlas Owner");
  await modal.getByLabel("بريد المالك").fill("owner@atlas-e2e.test");
  await modal.getByLabel("كلمة مرور المالك").fill("AtlasRelease123!");
  await modal.getByLabel("الخطة").selectOption("starter");
  await modal.getByRole("button", { name: "إنشاء الشركة" }).click();

  await expect(page.getByText("تم إنشاء الشركة ومساحة العمل وحساب المالك.")).toBeVisible();
  await expect(page.getByRole("button", { name: /ATLAS E2E/ })).toBeVisible();

  await page.getByLabel("الحالة").selectOption("suspended");
  await page.getByRole("button", { name: "حفظ إعدادات الشركة" }).click();
  await expect(page.getByText("تم تحديث إعدادات الشركة.")).toBeVisible();
  await expect(page.locator(".tenantInspector .status-suspended")).toBeVisible();
});

test("white-label SEO workspace creates site, schema and guarded dry-run plan", async ({ page, isMobile }) => {
  if (isMobile) test.skip();

  await page.goto("/");
  await page.getByLabel("معرّف الشركة").fill("nexvary-test");
  await page.getByLabel("البريد الإلكتروني").fill("owner@nexvary.test");
  await page.getByLabel("كلمة المرور").fill("ReleaseGate123!");
  await page.getByRole("button", { name: "تسجيل الدخول" }).click();
  await expect(page.getByText("مركز قيادة المبيعات")).toBeVisible();

  await page.getByRole("button", { name: "SEO Autopilot" }).click();
  await expect(page.getByText("WHITE-LABEL SEO ENGINE")).toBeVisible();

  await page.getByPlaceholder("اسم الموقع").fill("SEO E2E Site");
  await page.getByPlaceholder("https://company.com").fill("https://example.com");
  await page.getByRole("button", { name: "إضافة" }).click();
  await expect(page.getByText("SEO E2E Site")).toBeVisible();

  await page.getByRole("button", { name: "Schema" }).click();
  const schemaForm = page.locator("form").filter({ hasText: "Structured Data" });
  await schemaForm.locator('textarea[name="visible_data"]').fill('{"name":"SEO E2E Realty","url":"https://example.com"}');
  await schemaForm.getByRole("button", { name: "بناء Schema" }).click();
  await expect(page.locator(".codeResult pre")).toContainText('"@type": "Organization"');

  await page.getByRole("button", { name: "Autopilot" }).click();
  const planForm = page.locator("form").filter({ hasText: "خطة تغيير محمية" });
  await planForm.locator('select[name="action"]').selectOption("title_change");
  await planForm.locator('textarea[name="before"]').fill('{"title":"Old"}');
  await planForm.locator('textarea[name="after"]').fill('{"title":"New"}');
  await planForm.locator('textarea[name="reason"]').fill("SEO release gate dry run");
  await planForm.getByRole("button", { name: "إنشاء Dry Run" }).click();

  await expect(page.getByText("تم إنشاء خطة تغيير Dry Run فقط. لم تتم الكتابة على الموقع.")).toBeVisible();
  await expect(page.getByText("review_required")).toBeVisible();
});

test("mobile layout exposes navigation and does not overflow core controls", async ({ page, isMobile }) => {
  if (!isMobile) test.skip();

  await page.goto("/");
  await expect(page.locator(".loginCard")).toBeVisible();

  const viewport = page.viewportSize();
  expect(viewport).not.toBeNull();
  const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
  expect(bodyWidth).toBeLessThanOrEqual((viewport?.width || 412) + 2);

  await expect(page.locator("button.loginLanguage")).toBeVisible();
});
