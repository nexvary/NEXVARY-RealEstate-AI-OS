import { expect, test } from "@playwright/test";

test("Growth Intelligence connects campaign journey audience media playbook and feedback", async ({ page, isMobile }) => {
  if (isMobile) test.skip();

  const dev = await page.request.post("/api/v1/auth/bootstrap-development");
  expect(dev.ok()).toBeTruthy();
  const session = await dev.json();
  const headers = { Authorization: `Bearer ${session.access_token}` };

  const lead = await page.request.post("/api/v1/leads", {
    headers,
    data: {
      full_name: "Growth E2E Lead",
      phone: "01077770001",
      source: "manual",
      preferred_city: "New Cairo",
      budget: 7000000,
      bedrooms: 3,
    },
  });
  expect(lead.ok()).toBeTruthy();

  const project = await page.request.post("/api/v1/projects", {
    headers,
    data: {
      name: "Growth E2E Project",
      city: "New Cairo",
      developer: "E2E Developer",
      description: "Verified E2E project description",
    },
  });
  expect(project.ok()).toBeTruthy();

  await page.goto("/");
  await page.getByRole("button", { name: "دخول/إنشاء مساحة التطوير بضغطة واحدة" }).click();
  await expect(page.getByText("مركز قيادة المبيعات")).toBeVisible();

  await page.getByRole("button", { name: "النمو والإسناد" }).click();
  await expect(page.getByText("GROWTH & SALES INTELLIGENCE")).toBeVisible();

  await page.getByRole("button", { name: "الحملات والإسناد" }).click();
  const campaignForm = page.locator("form").filter({ hasText: "حملة جديدة" });
  await campaignForm.getByLabel("الاسم").fill("Growth E2E Campaign");
  await campaignForm.getByLabel("القناة").selectOption("facebook");
  await campaignForm.getByLabel("الحالة").selectOption("active");
  await campaignForm.getByLabel("الميزانية").fill("2500");
  await campaignForm.getByLabel("الإنفاق الفعلي").fill("900");
  await campaignForm.getByRole("button", { name: "إنشاء الحملة" }).click();
  await expect(page.getByText("تم إنشاء الحملة.")).toBeVisible();
  await expect(page.getByText("Growth E2E Campaign")).toBeVisible();

  await page.getByRole("button", { name: "رحلات العملاء" }).click();
  const journeyForm = page.locator("form").filter({ hasText: "تسجيل نقطة رحلة" });
  await journeyForm.getByLabel("العميل").selectOption({ label: /Growth E2E Lead/ });
  await journeyForm.getByLabel("الحملة").selectOption({ label: "Growth E2E Campaign" });
  await journeyForm.getByLabel("الحدث").selectOption("campaign_touch");
  await journeyForm.getByLabel("القناة").fill("facebook");
  await journeyForm.getByRole("button", { name: "تسجيل الحدث" }).click();
  await expect(page.getByText("تم تسجيل نقطة الرحلة.")).toBeVisible();
  await expect(page.locator(".journeyTimeline").getByText("campaign_touch")).toBeVisible();

  await page.getByRole("button", { name: "الجمهور 360" }).click();
  const audienceForm = page.locator("form").filter({ hasText: "شريحة جمهور جديدة" });
  await audienceForm.getByLabel("الاسم").fill("Growth E2E Audience");
  await audienceForm.getByLabel("المصادر مفصولة بفاصلة").fill("manual");
  await audienceForm.getByLabel("أقل Score").fill("0");
  await audienceForm.getByLabel("المدينة").fill("New Cairo");
  await audienceForm.getByRole("button", { name: "حفظ الشريحة" }).click();
  await expect(page.getByText("تم حفظ شريحة الجمهور.")).toBeVisible();

  await page.getByRole("button", { name: "مكتبة الوسائط" }).click();
  const mediaForm = page.locator("form").filter({ hasText: "إضافة أصل حقيقي" });
  await mediaForm.getByLabel("المشروع").selectOption({ label: /Growth E2E Project/ });
  await mediaForm.getByLabel("العنوان").fill("Growth E2E Brochure");
  await mediaForm.getByLabel("النوع").selectOption("pdf");
  await mediaForm.getByLabel("المصدر").selectOption("verified");
  await mediaForm.getByLabel("URL").fill("https://example.com/growth-e2e-brochure.pdf");
  await mediaForm.getByLabel("تم التحقق من الأصل").check();
  await mediaForm.getByRole("button", { name: "إضافة للمكتبة" }).click();
  await expect(page.getByText("تمت إضافة الأصل إلى مكتبة الوسائط.")).toBeVisible();
  await expect(page.getByText("Growth E2E Brochure")).toBeVisible();

  await page.getByRole("button", { name: "دليل الإجراءات" }).click();
  const playbookForm = page.locator("form").filter({ hasText: "دليل إجراءات جديد" });
  await playbookForm.getByLabel("الاسم").fill("Growth E2E Playbook");
  await playbookForm.getByLabel("يظهر عند مرحلة").selectOption("viewing");
  await playbookForm.getByLabel("الخطوات — سطر لكل خطوة").fill("أكد الوحدة\nأرسل الوسائط الموثقة\nحدد المتابعة");
  await playbookForm.getByRole("button", { name: "حفظ الدليل" }).click();
  await expect(page.getByText("تم حفظ دليل إجراءات المبيعات.")).toBeVisible();

  await page.getByRole("button", { name: "صوت العميل" }).click();
  const feedbackForm = page.locator("form").filter({ hasText: "تسجيل رأي العميل" });
  await feedbackForm.getByLabel("العميل").selectOption({ label: "Growth E2E Lead" });
  await feedbackForm.getByLabel("القناة").fill("whatsapp");
  await feedbackForm.getByLabel("التقييم 1-5").fill("5");
  await feedbackForm.getByLabel("الملاحظة").fill("تجربة المعاينة واضحة وسريعة");
  await feedbackForm.getByRole("button", { name: "حفظ الرأي" }).click();
  await expect(page.getByText("تم تسجيل صوت العميل.")).toBeVisible();
  await expect(page.getByText("تجربة المعاينة واضحة وسريعة")).toBeVisible();
});
