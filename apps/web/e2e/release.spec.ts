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
  await expect(page.locator(".app")).toHaveAttribute("dir", "rtl");
  await expect(page.locator(".sidebar")).toBeVisible();
  await expect(page.getByTestId("digital-clock")).toBeVisible();

  const layout = await page.locator(".app").evaluate((el) => {
    const app = el.getBoundingClientRect();
    const side = el.querySelector(".sidebar")?.getBoundingClientRect();
    return side ? { appLeft: app.left, appRight: app.right, sideLeft: side.left, sideRight: side.right } : null;
  });
  expect(layout).not.toBeNull();
  expect((layout?.appRight || 0) - (layout?.sideRight || 0)).toBeLessThan(3);
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
  await expect(page.locator(".pageHeading h1").filter({ hasText: "العملاء المحتملون" })).toBeVisible();

  await page.getByRole("button", { name: "رجوع" }).click();
  await expect(page.getByText("مركز قيادة المبيعات")).toBeVisible();

  await page.getByTitle("Language").click();
  await expect(page.getByText("Sales Command Center")).toBeVisible();
});

test("desktop development workspace is one-click and survives normal tenant presence", async ({ page, isMobile }) => {
  if (isMobile) test.skip();

  await page.goto("/");
  await expect(page.getByRole("button", { name: "دخول/إنشاء مساحة التطوير بضغطة واحدة" })).toBeVisible();
  await page.getByRole("button", { name: "دخول/إنشاء مساحة التطوير بضغطة واحدة" }).click();
  await expect(page.getByText("مركز قيادة المبيعات")).toBeVisible();

  await page.getByRole("button", { name: "تسجيل الخروج" }).click();
  await expect(page.getByRole("button", { name: "دخول/إنشاء مساحة التطوير بضغطة واحدة" })).toBeVisible();
  await page.getByRole("button", { name: "دخول/إنشاء مساحة التطوير بضغطة واحدة" }).click();
  await expect(page.getByText("مركز قيادة المبيعات")).toBeVisible();
});

test("system and company about sections are separate and reachable with internal back navigation", async ({ page, isMobile }) => {
  if (isMobile) test.skip();

  await page.goto("/");
  await page.getByLabel("معرّف الشركة").fill("nexvary-test");
  await page.getByLabel("البريد الإلكتروني").fill("owner@nexvary.test");
  await page.getByLabel("كلمة المرور").fill("ReleaseGate123!");
  await page.getByRole("button", { name: "تسجيل الدخول" }).click();

  await page.getByRole("button", { name: "عن النظام" }).click();
  await expect(page.locator(".pageHeading h1").filter({ hasText: "عن النظام" })).toBeVisible();
  await expect(page.getByText("CRM والمبيعات")).toBeVisible();
  await expect(page.getByText("White-Label وSaaS")).toBeVisible();
  await expect(page.getByRole("link", { name: "NEXVARY" })).toBeVisible();

  await page.getByRole("button", { name: "عن الشركة" }).click();
  await expect(page.getByRole("heading", { name: "NEXVARY Realty" })).toBeVisible();
  await expect(page.getByText("بيانات وهوية الشركة الحالية داخل منصة NEXVARY White-Label.")).toBeVisible();
  await expect(page.locator(".companyHeroCover")).toBeVisible();
  await expect(page.locator(".companyCoverLogo img")).toBeVisible();

  await page.getByRole("button", { name: "رجوع" }).click();
  await expect(page.locator(".pageHeading h1").filter({ hasText: "عن النظام" })).toBeVisible();
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

  await page.locator(".platformTenantForm").getByLabel("الحالة").selectOption("suspended");
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
  await page.getByRole("button", { name: "إضافة", exact: true }).click();
  await expect(page.getByRole("heading", { name: "SEO E2E Site", exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Schema", exact: true }).click();
  const schemaForm = page.locator("form").filter({ hasText: "Structured Data" });
  await schemaForm.locator('textarea[name="visible_data"]').fill('{"name":"SEO E2E Realty","url":"https://example.com"}');
  await schemaForm.getByRole("button", { name: "بناء Schema" }).click();
  await expect(page.locator(".codeResult pre")).toContainText('"@type": "Organization"');

  await page.getByRole("button", { name: "Autopilot", exact: true }).click();
  const planForm = page.locator("form").filter({ hasText: "خطة تغيير محمية" });
  await planForm.locator('select[name="action"]').selectOption("title_change");
  await planForm.locator('textarea[name="before"]').fill('{"title":"Old"}');
  await planForm.locator('textarea[name="after"]').fill('{"title":"New"}');
  await planForm.locator('textarea[name="reason"]').fill("SEO release gate dry run");
  await planForm.getByRole("button", { name: "إنشاء Dry Run" }).click();

  await expect(page.getByText("تم إنشاء خطة تغيير Dry Run فقط. لم تتم الكتابة على الموقع.")).toBeVisible();
  await expect(page.getByText("review_required")).toBeVisible();
});

test("commercial platform creates a reusable tenant template and provisions a company", async ({ page, isMobile }) => {
  if (isMobile) test.skip();

  await page.goto("/");
  await page.getByRole("button", { name: "إدارة منصة NEXVARY والشركات" }).click();
  await page.getByLabel("البريد الإلكتروني").fill("owner@nexvary.test");
  await page.getByLabel("كلمة المرور").fill("ReleaseGate123!");
  await page.getByRole("button", { name: "دخول إدارة المنصة" }).click();
  await expect(page.getByText("الاشتراكات والفواتير وقوالب الشركات")).toBeVisible();

  const templateForm = page.locator("form").filter({ hasText: "إنشاء قالب شركة" });
  await templateForm.getByLabel("اسم القالب").fill("E2E Commercial Pro");
  await templateForm.getByLabel("الاشتراك").fill("249");
  await templateForm.getByRole("button", { name: "حفظ القالب" }).click();
  await expect(page.getByText("تم حفظ قالب الشركة.")).toBeVisible();

  const provisionForm = page.locator("form").filter({ hasText: "إنشاء شركة بضغطة واحدة" });
  await provisionForm.getByLabel("القالب").selectOption({ label: "E2E Commercial Pro · professional" });
  await provisionForm.getByLabel("اسم الشركة").fill("Commercial E2E Realty");
  await provisionForm.getByLabel("المعرّف").fill("commercial-e2e");
  await provisionForm.getByLabel("الاسم التجاري").fill("COMMERCIAL E2E");
  await provisionForm.getByLabel("اسم المالك").fill("Commercial Owner");
  await provisionForm.getByLabel("بريد المالك").fill("owner@commercial-e2e.test");
  await provisionForm.getByLabel("كلمة المرور").fill("CommercialRelease123!");
  await provisionForm.getByRole("button", { name: "إنشاء الشركة كاملة" }).click();

  await expect(page.getByText(/تم إنشاء الشركة commercial-e2e بالكامل/)).toBeVisible();
  await expect(page.getByRole("button", { name: /COMMERCIAL E2E/ })).toBeVisible();
});

test("bank-transfer billing requires platform verification before payment", async ({ page, isMobile }) => {
  if (isMobile) test.skip();

  await page.goto("/");
  await page.getByRole("button", { name: "إدارة منصة NEXVARY والشركات" }).click();
  await page.getByLabel("البريد الإلكتروني").fill("owner@nexvary.test");
  await page.getByLabel("كلمة المرور").fill("ReleaseGate123!");
  await page.getByRole("button", { name: "دخول إدارة المنصة" }).click();

  await page.getByRole("button", { name: /NEXVARY Realty/ }).first().click();

  const bankForm = page.locator("form").filter({ hasText: "إضافة حساب بنكي" });
  await bankForm.getByLabel("اسم مختصر").fill("NEXVARY E2E EGP");
  await bankForm.getByLabel("اسم البنك").fill("E2E Bank");
  await bankForm.getByLabel("اسم صاحب الحساب").fill("NEXVARY");
  await bankForm.getByLabel("رقم الحساب").fill("001122334455");
  await bankForm.getByLabel("العملة").fill("EGP");
  await bankForm.getByRole("button", { name: "حفظ الحساب" }).click();
  await expect(page.getByText("تم حفظ الحساب البنكي.")).toBeVisible();

  const invoiceForm = page.locator("form").filter({ hasText: "فاتورة جديدة" });
  await invoiceForm.getByLabel("المبلغ").fill("5000");
  await invoiceForm.getByLabel("الضريبة").fill("0");
  await invoiceForm.getByLabel("العملة").fill("EGP");
  await invoiceForm.getByLabel("الوصف").fill("E2E bank transfer invoice");
  await invoiceForm.getByRole("button", { name: "إنشاء الفاتورة" }).click();
  await expect(page.getByText("تم إنشاء الفاتورة.")).toBeVisible();

  await page.goto("/");
  await page.getByLabel("معرّف الشركة").fill("nexvary-test");
  await page.getByLabel("البريد الإلكتروني").fill("owner@nexvary.test");
  await page.getByLabel("كلمة المرور").fill("ReleaseGate123!");
  await page.getByRole("button", { name: "تسجيل الدخول" }).click();

  await page.getByRole("button", { name: "الاشتراك والتحويل البنكي" }).click();
  await expect(page.getByText("الدفع يتم بتحويل بنكي فقط. بعد التحويل أرسل رقم العملية هنا، ويعتمد مسؤول المنصة الدفع بعد مراجعته.")).toBeVisible();

  const invoiceButton = page.locator(".billingInvoice").filter({ hasText: "E2E bank transfer invoice" });
  await invoiceButton.click();
  const transferForm = page.locator("form").filter({ hasText: "تسجيل تحويل بنكي" });
  await transferForm.getByLabel("اسم المحول").fill("NEXVARY Test Realty");
  await transferForm.getByLabel("بنك المحول").fill("Sender Bank");
  await transferForm.getByLabel("رقم العملية/مرجع التحويل").fill("E2E-BANK-TRANSFER-001");
  await transferForm.getByRole("button", { name: "إرسال للتحقق" }).click();

  await expect(page.getByText("تم إرسال بيانات التحويل للمراجعة. لن تُعتبر الفاتورة مدفوعة إلا بعد اعتماد التحويل.")).toBeVisible();
  await expect(page.locator(".billingInvoice").filter({ hasText: "E2E bank transfer invoice" }).locator(".status-pending_verification")).toBeVisible();

  await page.getByRole("button", { name: "تسجيل الخروج" }).click();
  await page.getByRole("button", { name: "إدارة منصة NEXVARY والشركات" }).click();
  await expect(page.getByText("الحسابات البنكية ومراجعة التحويلات")).toBeVisible();

  const transferRow = page.locator(".transferReviewRows article").filter({ hasText: "E2E-BANK-TRANSFER-001" });
  await expect(transferRow).toBeVisible();
  await transferRow.getByRole("button", { name: "اعتماد" }).click();
  await expect(page.getByText("تم اعتماد التحويل وتسجيل الفاتورة مدفوعة.")).toBeVisible();
});

test("tenant WhatsApp channel configuration is usable without exposing secrets", async ({ page, isMobile }) => {
  if (isMobile) test.skip();

  await page.goto("/");
  await page.getByLabel("معرّف الشركة").fill("nexvary-test");
  await page.getByLabel("البريد الإلكتروني").fill("owner@nexvary.test");
  await page.getByLabel("كلمة المرور").fill("ReleaseGate123!");
  await page.getByRole("button", { name: "تسجيل الدخول" }).click();

  await page.getByRole("button", { name: "قنوات WhatsApp" }).click();
  await expect(page.getByText("قنوات WhatsApp الخاصة بالشركة")).toBeVisible();

  const form = page.locator("form").filter({ hasText: "إضافة قناة" });
  await form.getByLabel("الاسم الظاهر").fill("E2E Sales WhatsApp");
  await form.getByLabel("Phone Number ID").fill("e2e-phone-123");
  await form.getByLabel("WABA ID").fill("e2e-waba-456");
  await form.getByLabel("رقم النشاط").fill("+201111111111");
  await form.getByLabel("Access Token").fill("e2e-secret-token");
  await form.getByLabel("App Secret").fill("e2e-app-secret");
  await form.getByRole("button", { name: "حفظ القناة" }).click();

  await expect(page.getByText("تم حفظ قناة WhatsApp ومفاتيحها بصورة مشفرة.")).toBeVisible();
  await expect(page.getByText("E2E Sales WhatsApp")).toBeVisible();
  await expect(page.getByText("e2e-secret-token")).toHaveCount(0);
  await page.getByRole("button", { name: "فحص الجاهزية" }).click();
  await expect(page.getByText(/القناة جاهزة للاستخدام/)).toBeVisible();
});

test("SEO Autopilot synchronizes real-estate project pages from live inventory data", async ({ page, isMobile }) => {
  if (isMobile) test.skip();

  await page.goto("/");
  await page.getByLabel("معرّف الشركة").fill("nexvary-test");
  await page.getByLabel("البريد الإلكتروني").fill("owner@nexvary.test");
  await page.getByLabel("كلمة المرور").fill("ReleaseGate123!");
  await page.getByRole("button", { name: "تسجيل الدخول" }).click();

  await page.getByRole("button", { name: "SEO Autopilot" }).click();
  await page.getByRole("button", { name: "SEO E2E Site" }).click();
  await page.getByRole("button", { name: "صفحات العقارات" }).click();

  await expect(page.getByText("صفحات المشروعات والوحدات العقارية")).toBeVisible();
  await page.getByLabel("المشروع العقاري").selectOption({ label: "بوابة القاهرة · New Cairo" });
  await page.getByRole("button", { name: "مزامنة المشروع وكل وحداته" }).click();

  await expect(page.getByText(/حقول مختلقة: 0/)).toBeVisible();
  await expect(page.getByText("SEO ready")).toBeVisible();
  await expect(page.getByText(/بوابة القاهرة — New Cairo/)).toBeVisible();
});

test("Automation Studio builds and runs a safe visual workflow", async ({ page, isMobile }) => {
  if (isMobile) test.skip();

  await page.goto("/");
  await page.getByLabel("معرّف الشركة").fill("nexvary-test");
  await page.getByLabel("البريد الإلكتروني").fill("owner@nexvary.test");
  await page.getByLabel("كلمة المرور").fill("ReleaseGate123!");
  await page.getByRole("button", { name: "تسجيل الدخول" }).click();

  await page.getByRole("button", { name: "Automation Studio" }).click();
  await expect(page.getByText("VISUAL AUTOMATION STUDIO")).toBeVisible();
  await expect(page.getByText(/لا يوجد PowerShell أو Shell مخفي/)).toBeVisible();

  const create = page.locator("form.automationCreate");
  await create.getByPlaceholder("اسم Workflow").fill("E2E Safe Automation");
  await create.getByPlaceholder("وصف مختصر").fill("Visual workflow release gate");
  await create.getByRole("button", { name: "جديد" }).click();

  await page.getByRole("button", { name: /تشغيل يدوي/ }).click();
  await page.getByRole("button", { name: /إنشاء مهمة/ }).click();
  await page.getByRole("button", { name: /إرجاع النتيجة/ }).click();

  await page.locator(".automationNode").filter({ hasText: "إنشاء مهمة" }).click();
  await page.getByLabel("إعدادات JSON").fill('{"title":"E2E Automation Task","notes":"Created by Automation Studio release gate","due_hours":1}');
  await page.getByRole("button", { name: "تطبيق الإعدادات" }).click();

  const composer = page.locator(".edgeComposer");
  await composer.locator("select").nth(0).selectOption({ label: "تشغيل يدوي" });
  await composer.locator("select").nth(1).selectOption({ label: "إنشاء مهمة" });
  await composer.getByRole("button", { name: "ربط" }).click();

  await composer.locator("select").nth(0).selectOption({ label: "إنشاء مهمة" });
  await composer.locator("select").nth(1).selectOption({ label: "إرجاع النتيجة" });
  await composer.getByRole("button", { name: "ربط" }).click();

  await page.getByRole("button", { name: "حفظ الرسم" }).click();
  await expect(page.getByText("تم حفظ الرسم والتحقق من عدم وجود حلقات.")).toBeVisible();

  await page.getByRole("button", { name: "Run Workflow" }).click();
  await expect(page.getByText(/انتهى التشغيل بالحالة: succeeded/)).toBeVisible();
  await expect(page.locator(".automationRuns article").first()).toContainText("succeeded");
  await expect(page.locator(".automationRuns article").first()).toContainText("3 nodes");

  await expect(page.getByRole("button", { name: "نسخ" })).toBeVisible();
  await expect(page.getByRole("button", { name: "حفظ الرسم" })).toBeDisabled();
});

test("omnichannel sales inbox keeps unverified replies behind human handoff", async ({ page, isMobile }) => {
  if (isMobile) test.skip();

  await page.goto("/");
  await page.getByLabel("معرّف الشركة").fill("nexvary-test");
  await page.getByLabel("البريد الإلكتروني").fill("owner@nexvary.test");
  await page.getByLabel("كلمة المرور").fill("ReleaseGate123!");
  await page.getByRole("button", { name: "تسجيل الدخول" }).click();

  await page.getByRole("button", { name: "المحادثات" }).click();
  await expect(page.getByText("GROUNDED OMNICHANNEL SALES")).toBeVisible();

  const creator = page.locator("form.salesConversationCreate");
  await creator.locator('select[name="channel"]').selectOption("whatsapp");
  await creator.locator('input[name="external_contact"]').fill("201099999999");
  await creator.locator('input[name="display_name"]').fill("عميل Omnichannel");
  await creator.getByRole("button", { name: "إضافة" }).click();

  await expect(page.getByText("عميل Omnichannel")).toBeVisible();
  await page.getByLabel("طريقة الرد").selectOption("voice");

  const replyForm = page.locator("form").filter({ hasText: "تجهيز رد مبيعات مؤكد" });
  await replyForm.getByLabel("سؤال العميل").fill("عايز فيلا 6 غرف في أسوان");
  await replyForm.getByLabel("المدينة").fill("Aswan");
  await replyForm.getByLabel("الغرف").fill("6");
  await replyForm.getByLabel("نوع الوحدة").fill("villa");
  await replyForm.getByRole("button", { name: "تجهيز الرد" }).click();

  await expect(page.getByText("لا توجد إجابة تجارية مؤكدة؛ تم إنشاء تحويل لموظف.")).toBeVisible();
  await expect(page.getByText("pending_approval")).toBeVisible();
  await expect(page.getByText(/مطلوب موظف|No currently available unit matched/)).toBeVisible();
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
