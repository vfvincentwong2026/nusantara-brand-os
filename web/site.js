/* Public homepage.
   Radar rows use only fields whose provenance is "x_public".
   Do not render Instagram, TikTok, or demo_estimate figures.
   Do not hard-code metrics. */
(function () {
  var MAIL = "ptxdirectionpublicrelations@gmail.com";
  var RADAR_URL = "trend/data/local_brands.json";
  var KEY = "nbo-public-lang";
  var TOP_N = 5;
  var LOCALE = { id: "id-ID", zh: "zh-CN", en: "en-US" };
  var lang = "id";
  var radarPayload = null;
  var radarFailed = false;

  var STR = {
    id: {
      "skip": "Langsung ke isi",
      "lang.group": "Bahasa",
      "lang.nav": "Navigasi",
      "nav.brand": "Merek",
      "nav.suppliers": "Pemasok",
      "nav.radar": "Contoh radar",
      "nav.about": "Tentang",
      "nav.contact": "Kontak",
      "nav.openRadar": "Buka radar",
      "nav.tools": "Alat",
      "hero.kicker": "PT XDirection Public Relations",
      "hero.title": "Catatan tentang merek kopi dan teh di Indonesia.",
      "hero.lead": "Merek bisa membaca radar panas dari data publik X, lalu meminta satu halaman perbandingan dengan kompetitor yang mereka sebut sendiri. Pemasok biji kopi, teh, bahan baku, peralatan, dan kemasan bisa mengajukan diri untuk masuk daftar.",
      "hero.operator": "Dioperasikan oleh PT XDirection Public Relations, perusahaan Indonesia.",
      "hero.ctaRadar": "Lihat contoh radar",
      "hero.ctaCompare": "Ajukan perbandingan",
      "hero.ctaSupplier": "Daftar sebagai pemasok",
      "brand.kicker": "01 — Merek",
      "brand.title": "Untuk merek yang sudah punya nama",
      "brand.radarTitle": "Radar panas media sosial",
      "brand.radarBody": "Daftar merek kopi dan teh yang dilacak, dengan metrik yang diambil dari data publik X. Instagram dan TikTok belum terhubung.",
      "brand.radarLink": "Buka radar lengkap",
      "brand.compareTitle": "Perbandingan kompetitor satu halaman",
      "brand.compareBody": "Ajukan satu halaman yang membandingkan merek Anda dengan merek pembanding yang Anda sebutkan. Pengajuan ini gratis. Situs ini tidak menyimpan formulir; tautan membuka aplikasi email Anda.",
      "brand.compareCta": "Ajukan lewat email",
      "brand.laterKicker": "Berikutnya",
      "brand.laterTitle": "Belum dibuka",
      "brand.later1": "Pengelolaan media sosial",
      "brand.later2": "Pustaka materi",
      "brand.later3": "Layanan pelanggan berbasis AI",
      "brand.laterNote": "Tiga layanan di atas belum menerima permintaan.",
      "supplier.kicker": "02 — Pemasok",
      "supplier.title": "Untuk pemasok bahan dan peralatan",
      "supplier.lead": "Pemasok bisa mengajukan diri agar namanya masuk daftar yang kami simpan.",
      "supplier.whoTitle": "Yang dapat mendaftar",
      "supplier.item1": "Biji kopi",
      "supplier.item2": "Teh",
      "supplier.item3": "Bahan baku",
      "supplier.item4": "Peralatan",
      "supplier.item5": "Kemasan",
      "supplier.howTitle": "Cara mendaftar",
      "supplier.howBody": "Kirim email dengan nama perusahaan, kategori, dan kota. Tidak ada formulir di situs ini.",
      "supplier.feeTitle": "Tahap awal",
      "supplier.feeBody": "Pada tahap awal, pendaftaran gratis.",
      "supplier.cta": "Daftar lewat email",
      "radar.kicker": "03 — Radar",
      "radar.title": "Contoh radar",
      "radar.lead": "Beberapa merek teratas menurut skor panas di berkas data. Tabel hanya memuat angka yang berstatus data publik X.",
      "radar.platforms": "Instagram dan TikTok belum terhubung. Angka kedua platform tidak ditampilkan.",
      "radar.directory": "Kota dan kategori adalah label pada daftar radar, bukan angka dari X.",
      "radar.loading": "Memuat data radar…",
      "radar.error": "Contoh radar tidak dapat dimuat dari berkas data. Buka halaman radar untuk melihat sumbernya.",
      "radar.empty": "Berkas data tidak berisi skor panas dari data publik X.",
      "radar.showing": "Menampilkan {n} merek teratas menurut skor panas X publik.",
      "radar.colBrand": "Merek",
      "radar.colAccount": "Akun X",
      "radar.colFollowers": "Pengikut X",
      "radar.colMentions": "Sebutan 7 hari",
      "radar.colHeat": "Skor panas",
      "radar.sourceLabel": "Catatan sumber pada berkas data",
      "radar.noteMissing": "Catatan sumber tidak ada di berkas data.",
      "radar.updated": "Tanggal unduh X: {fetched}. Berkas dibuat: {generated}.",
      "radar.updatedMissing": "Tanggal pembaruan tidak ada di berkas data.",
      "radar.open": "Buka radar lengkap",
      "about.kicker": "04 — Tentang",
      "about.title": "Tentang kami",
      "about.body": "Nusantara Brand OS dijalankan oleh PT XDirection Public Relations, perusahaan di Indonesia. Kerja kami sekarang sederhana: membaca data publik tentang merek kopi dan teh, menulis perbandingan satu halaman bila diminta, dan menerima pendaftaran pemasok.",
      "contact.kicker": "05 — Kontak",
      "contact.title": "Kontak",
      "contact.body": "Satu-satunya saluran di situs ini adalah email. Tidak ada formulir dan tidak ada nomor telepon.",
      "contact.emailLabel": "Email",
      "contact.compare": "Ajukan perbandingan kompetitor",
      "contact.supplier": "Daftar sebagai pemasok",
      "footer.note": "PT XDirection Public Relations · Nusantara Brand OS",
      "footer.privacy": "Kebijakan privasi",
      "footer.terms": "Ketentuan layanan",
      "footer.radar": "Radar",
      "footer.tools": "Alat",
      "meta.title": "Nusantara Brand OS · Catatan kopi dan teh Indonesia",
      "meta.description": "Catatan untuk merek dan pemasok kopi serta teh di Indonesia. Dioperasikan oleh PT XDirection Public Relations."
    },
    zh: {
      "skip": "跳到正文",
      "lang.group": "语言",
      "lang.nav": "导航",
      "nav.brand": "品牌",
      "nav.suppliers": "供应商",
      "nav.radar": "雷达样例",
      "nav.about": "关于",
      "nav.contact": "联系",
      "nav.openRadar": "打开雷达",
      "nav.tools": "工具",
      "hero.kicker": "PT XDirection Public Relations",
      "hero.title": "一份关于印尼咖啡与茶饮品牌的笔记。",
      "hero.lead": "品牌可以查看来自 X 公开数据的热度，并用邮件申请一页纸，把自己和点名的竞品放在一起。咖啡豆、茶叶、原料、设备、包材的供应商可以申请列入名单。",
      "hero.operator": "运营主体为印尼公司 PT XDirection Public Relations。",
      "hero.ctaRadar": "查看雷达样例",
      "hero.ctaCompare": "申请竞品对比",
      "hero.ctaSupplier": "供应商入驻",
      "brand.kicker": "01 — 品牌",
      "brand.title": "给已经有名字的品牌",
      "brand.radarTitle": "本地品牌社媒热度雷达",
      "brand.radarBody": "展示正在追踪的咖啡与茶饮品牌，以及来自 X 公开数据的指标。Instagram 与 TikTok 尚未接通。",
      "brand.radarLink": "打开完整雷达",
      "brand.compareTitle": "一页纸竞品对比",
      "brand.compareBody": "可以免费申请一页纸，把你的品牌和你点名的竞品放在一起看。本站不保存表单，点击后在邮件客户端中打开。",
      "brand.compareCta": "用邮件申请",
      "brand.laterKicker": "后续",
      "brand.laterTitle": "尚未开通",
      "brand.later1": "社媒代运营",
      "brand.later2": "素材库",
      "brand.later3": "AI 客服",
      "brand.laterNote": "以上三项目前不接受委托。",
      "supplier.kicker": "02 — 供应商",
      "supplier.title": "给原料和设备的供应商",
      "supplier.lead": "供应商可以来信，请我们把公司记进名单。",
      "supplier.whoTitle": "可入驻类别",
      "supplier.item1": "咖啡豆",
      "supplier.item2": "茶叶",
      "supplier.item3": "原料",
      "supplier.item4": "设备",
      "supplier.item5": "包材",
      "supplier.howTitle": "如何申请",
      "supplier.howBody": "发送邮件，写明公司名称、类别和城市。本站没有表单。",
      "supplier.feeTitle": "起步阶段",
      "supplier.feeBody": "起步阶段免费入驻。",
      "supplier.cta": "用邮件申请入驻",
      "radar.kicker": "03 — 雷达",
      "radar.title": "雷达样例",
      "radar.lead": "按数据文件中的热度分数列出靠前的品牌。表格只显示标记为 X 公开数据的数字。",
      "radar.platforms": "Instagram 与 TikTok 尚未接通，不展示这两个平台的数字。",
      "radar.directory": "城市和品类是雷达名单中的标签，不是 X 的数字。",
      "radar.loading": "正在读取雷达数据…",
      "radar.error": "无法从数据文件加载雷达样例。请打开雷达页面查看原始数据。",
      "radar.empty": "数据文件里没有来自 X 公开数据的热度分数。",
      "radar.showing": "按 X 公开热度显示前 {n} 个品牌。",
      "radar.colBrand": "品牌",
      "radar.colAccount": "X 账号",
      "radar.colFollowers": "X 粉丝",
      "radar.colMentions": "近 7 天提及",
      "radar.colHeat": "热度",
      "radar.sourceLabel": "数据文件中的来源说明",
      "radar.noteMissing": "数据文件里没有来源说明。",
      "radar.updated": "X 数据下载时间：{fetched}。文件生成时间：{generated}。",
      "radar.updatedMissing": "数据文件里没有更新日期。",
      "radar.open": "打开完整雷达",
      "about.kicker": "04 — 关于",
      "about.title": "关于我们",
      "about.body": "Nusantara Brand OS 由印尼公司 PT XDirection Public Relations 运营。眼下的工作不多：读咖啡与茶饮品牌的公开数据，应要求写一页纸对比，并接收供应商的入驻来信。",
      "contact.kicker": "05 — 联系",
      "contact.title": "联系",
      "contact.body": "本站只提供电子邮件。没有表单，也没有电话号码。",
      "contact.emailLabel": "邮箱",
      "contact.compare": "申请竞品对比",
      "contact.supplier": "申请供应商入驻",
      "footer.note": "PT XDirection Public Relations · Nusantara Brand OS",
      "footer.privacy": "隐私政策",
      "footer.terms": "服务条款",
      "footer.radar": "雷达",
      "footer.tools": "工具",
      "meta.title": "Nusantara Brand OS · 印尼咖啡与茶饮笔记",
      "meta.description": "给印尼咖啡与茶饮品牌和供应商的笔记。运营主体为 PT XDirection Public Relations。"
    },
    en: {
      "skip": "Skip to content",
      "lang.group": "Language",
      "lang.nav": "Navigation",
      "nav.brand": "Brands",
      "nav.suppliers": "Suppliers",
      "nav.radar": "Radar sample",
      "nav.about": "About",
      "nav.contact": "Contact",
      "nav.openRadar": "Open radar",
      "nav.tools": "Tools",
      "hero.kicker": "PT XDirection Public Relations",
      "hero.title": "Notes on coffee and tea brands in Indonesia.",
      "hero.lead": "A brand can read a heat radar drawn from public X data, then ask by email for one page set beside competitors it names. Suppliers of coffee beans, tea, ingredients, equipment, and packaging can ask to be listed.",
      "hero.operator": "Operated by PT XDirection Public Relations, an Indonesian company.",
      "hero.ctaRadar": "View the radar sample",
      "hero.ctaCompare": "Request a comparison",
      "hero.ctaSupplier": "List as a supplier",
      "brand.kicker": "01 — Brands",
      "brand.title": "For brands that already have a name",
      "brand.radarTitle": "Social heat radar",
      "brand.radarBody": "Tracked coffee and tea brands, with figures taken from public X data. Instagram and TikTok are not connected.",
      "brand.radarLink": "Open the full radar",
      "brand.compareTitle": "One-page competitor comparison",
      "brand.compareBody": "Request one page that sets your brand next to competitors you name. The request is free of charge. This site does not store a form; the link opens in your email app.",
      "brand.compareCta": "Request by email",
      "brand.laterKicker": "Later",
      "brand.laterTitle": "Not open yet",
      "brand.later1": "Social media management",
      "brand.later2": "Asset library",
      "brand.later3": "AI customer service",
      "brand.laterNote": "These three are not taking requests.",
      "supplier.kicker": "02 — Suppliers",
      "supplier.title": "For suppliers of ingredients and equipment",
      "supplier.lead": "A supplier can write and ask us to keep the company name on the list.",
      "supplier.whoTitle": "Who can apply",
      "supplier.item1": "Coffee beans",
      "supplier.item2": "Tea",
      "supplier.item3": "Ingredients",
      "supplier.item4": "Equipment",
      "supplier.item5": "Packaging",
      "supplier.howTitle": "How to apply",
      "supplier.howBody": "Send an email with the company name, category, and city. There is no form on this site.",
      "supplier.feeTitle": "Early stage",
      "supplier.feeBody": "At this early stage, listing is free of charge.",
      "supplier.cta": "Apply by email",
      "radar.kicker": "03 — Radar",
      "radar.title": "Radar sample",
      "radar.lead": "The highest heat scores in the data file. The table shows only figures marked as public X data.",
      "radar.platforms": "Instagram and TikTok are not connected. Figures from those platforms are not shown.",
      "radar.directory": "City and category are labels from the radar list, not X figures.",
      "radar.loading": "Loading radar data…",
      "radar.error": "The radar sample could not be loaded from the data file. Open the radar page to see the source.",
      "radar.empty": "The data file has no heat score from public X data.",
      "radar.showing": "Showing the top {n} brands by public X heat.",
      "radar.colBrand": "Brand",
      "radar.colAccount": "X account",
      "radar.colFollowers": "X followers",
      "radar.colMentions": "Mentions, 7 days",
      "radar.colHeat": "Heat",
      "radar.sourceLabel": "Source note in the data file",
      "radar.noteMissing": "The data file has no source note.",
      "radar.updated": "X download time: {fetched}. File generated: {generated}.",
      "radar.updatedMissing": "The data file has no update time.",
      "radar.open": "Open the full radar",
      "about.kicker": "04 — About",
      "about.title": "About",
      "about.body": "Nusantara Brand OS is run by PT XDirection Public Relations, a company in Indonesia. The work at the moment is small: read public data on coffee and tea brands, write a one-page comparison when asked, and take letters from suppliers.",
      "contact.kicker": "05 — Contact",
      "contact.title": "Contact",
      "contact.body": "Email is the only channel on this site. There is no form and no phone number.",
      "contact.emailLabel": "Email",
      "contact.compare": "Request a competitor comparison",
      "contact.supplier": "Apply as a supplier",
      "footer.note": "PT XDirection Public Relations · Nusantara Brand OS",
      "footer.privacy": "Privacy policy",
      "footer.terms": "Terms of service",
      "footer.radar": "Radar",
      "footer.tools": "Tools",
      "meta.title": "Nusantara Brand OS · Notes on coffee and tea in Indonesia",
      "meta.description": "Notes for coffee and tea brands and suppliers in Indonesia. Operated by PT XDirection Public Relations."
    }
  };

  var MAILTO = {
    id: {
      compare: {
        subject: "Permintaan perbandingan kompetitor satu halaman",
        body: "Nama merek:\nKota:\nKategori:\nMerek pembanding:\n"
      },
      supplier: {
        subject: "Pendaftaran pemasok Nusantara Brand OS",
        body: "Nama perusahaan:\nKategori (biji kopi / teh / bahan baku / peralatan / kemasan):\nKota:\n"
      }
    },
    zh: {
      compare: {
        subject: "一页纸竞品对比申请",
        body: "品牌名称：\n城市：\n品类：\n对比品牌：\n"
      },
      supplier: {
        subject: "供应商入驻申请",
        body: "公司名称：\n类别（咖啡豆 / 茶叶 / 原料 / 设备 / 包材）：\n城市：\n"
      }
    },
    en: {
      compare: {
        subject: "One-page competitor comparison request",
        body: "Brand name:\nCity:\nCategory:\nBrands to compare:\n"
      },
      supplier: {
        subject: "Supplier listing request",
        body: "Company name:\nCategory (coffee beans / tea / ingredients / equipment / packaging):\nCity:\n"
      }
    }
  };

  var CITY = {
    "雅加达": { id: "Jakarta", zh: "雅加达", en: "Jakarta" },
    "泗水": { id: "Surabaya", zh: "泗水", en: "Surabaya" },
    "万隆": { id: "Bandung", zh: "万隆", en: "Bandung" },
    "日惹": { id: "Yogyakarta", zh: "日惹", en: "Yogyakarta" },
    "巴厘巴板": { id: "Balikpapan", zh: "巴厘巴板", en: "Balikpapan" },
    "登巴萨": { id: "Denpasar", zh: "登巴萨", en: "Denpasar" },
    "马那多": { id: "Manado", zh: "马那多", en: "Manado" },
    "未核实": { id: "Belum diverifikasi", zh: "未核实", en: "Unverified" }
  };

  var CATEGORY = {
    "冻酸奶甜品": { id: "Hidangan yogurt beku", zh: "冻酸奶甜品", en: "Frozen yogurt dessert" },
    "台式奶茶": { id: "Teh susu gaya Taiwan", zh: "台式奶茶", en: "Taiwanese-style milk tea" },
    "咖啡": { id: "Kopi", zh: "咖啡", en: "Coffee" },
    "奶茶": { id: "Teh susu", zh: "奶茶", en: "Milk tea" },
    "现制咖啡": { id: "Kopi racik", zh: "现制咖啡", en: "Made-to-order coffee" },
    "现制茶饮": { id: "Teh racik", zh: "现制茶饮", en: "Made-to-order tea" },
    "现烤烘焙": { id: "Roti panggang", zh: "现烤烘焙", en: "Freshly baked goods" },
    "综合现制饮品": { id: "Minuman racik campuran", zh: "综合现制饮品", en: "Mixed made-to-order drinks" },
    "芝士熟食快餐": { id: "Makanan cepat saji keju", zh: "芝士熟食快餐", en: "Cheese quick-service food" }
  };

  function t(key) {
    var pack = STR[lang] || STR.id;
    if (Object.prototype.hasOwnProperty.call(pack, key)) return pack[key];
    if (Object.prototype.hasOwnProperty.call(STR.id, key)) return STR.id[key];
    return key;
  }

  function directoryLabel(map, raw) {
    if (typeof raw !== "string" || !raw.trim()) return "";
    var row = map[raw];
    if (!row || !row[lang]) return raw;
    return row[lang];
  }

  function publicNumber(row, key) {
    if (!row || !row.provenance || row.provenance[key] !== "x_public") return null;
    var value = row[key];
    if (typeof value !== "number" || !isFinite(value)) return null;
    return value;
  }

  function publicHandle(row) {
    if (!row || !row.provenance || row.provenance.x !== "x_public") return null;
    if (typeof row.x !== "string" || !/^@[A-Za-z0-9_]+$/.test(row.x)) return null;
    return row.x;
  }

  function topRows(data) {
    var brands = data && Array.isArray(data.brands) ? data.brands : [];
    return brands.filter(function (row) {
      return row && publicNumber(row, "heat") !== null && typeof row.name === "string" && row.name.trim();
    }).sort(function (a, b) {
      return publicNumber(b, "heat") - publicNumber(a, "heat") || a.name.localeCompare(b.name);
    }).slice(0, TOP_N);
  }

  function formatInt(value) {
    return new Intl.NumberFormat(LOCALE[lang] || "id-ID", { maximumFractionDigits: 0 }).format(value);
  }

  function formatHeat(value) {
    return new Intl.NumberFormat(LOCALE[lang] || "id-ID", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 1
    }).format(value);
  }

  function mailto(kind) {
    var pack = MAILTO[lang] && MAILTO[lang][kind];
    if (!pack) return "mailto:" + MAIL;
    return "mailto:" + MAIL + "?subject=" + encodeURIComponent(pack.subject) + "&body=" + encodeURIComponent(pack.body);
  }

  function dateLine(data) {
    var fetched = data.x_snapshot && typeof data.x_snapshot.fetched_at === "string" ? data.x_snapshot.fetched_at : "";
    var generated = typeof data.generated_at === "string" ? data.generated_at : "";
    if (!fetched && !generated) return t("radar.updatedMissing");
    return t("radar.updated").replace("{fetched}", fetched || "—").replace("{generated}", generated || "—");
  }

  function textCell(text, label, numeric) {
    var td = document.createElement("td");
    td.dataset.label = label;
    if (numeric) td.className = "num";
    td.textContent = text;
    return td;
  }

  function brandCell(row, label) {
    var td = document.createElement("td");
    td.dataset.label = label;
    var wrap = document.createElement("div");
    wrap.className = "brand-cell";
    var name = document.createElement("span");
    name.className = "brand-name";
    name.textContent = row.name.trim();
    wrap.appendChild(name);
    var bits = [];
    var city = directoryLabel(CITY, row.city);
    var category = directoryLabel(CATEGORY, row.category);
    if (city) bits.push(city);
    if (category) bits.push(category);
    if (bits.length) {
      var meta = document.createElement("span");
      meta.className = "brand-meta";
      meta.textContent = bits.join(" · ");
      wrap.appendChild(meta);
    }
    td.appendChild(wrap);
    return td;
  }

  function heatCell(row, label) {
    var td = document.createElement("td");
    td.dataset.label = label;
    td.className = "num";
    var heat = publicNumber(row, "heat");
    var fig = document.createElement("span");
    fig.className = "heat-fig";
    var num = document.createElement("span");
    num.textContent = heat === null ? "—" : formatHeat(heat);
    var track = document.createElement("span");
    track.className = "rule-bar";
    var fill = document.createElement("span");
    if (heat !== null) fill.style.width = Math.max(6, Math.round(heat)) + "%";
    track.appendChild(fill);
    fig.appendChild(num);
    fig.appendChild(track);
    td.appendChild(fig);
    return td;
  }

  function shownNumber(row, key, format) {
    var value = publicNumber(row, key);
    return value === null ? "—" : format(value);
  }

  function renderRadar() {
    var status = document.getElementById("radar-status");
    var summary = document.getElementById("radar-summary");
    var source = document.getElementById("radar-source");
    var updated = document.getElementById("radar-updated");
    var body = document.getElementById("radar-rows");
    if (!status || !body) return;
    body.replaceChildren();
    if (radarFailed) {
      status.textContent = t("radar.error");
      summary.textContent = "";
      source.textContent = "";
      updated.textContent = "";
      return;
    }
    if (!radarPayload) {
      status.textContent = t("radar.loading");
      return;
    }
    var rows = topRows(radarPayload);
    status.textContent = rows.length ? "" : t("radar.empty");
    summary.textContent = t("radar.showing").replace("{n}", String(rows.length));
    source.textContent = typeof radarPayload.source_note === "string" && radarPayload.source_note.trim()
      ? radarPayload.source_note.trim()
      : t("radar.noteMissing");
    updated.textContent = dateLine(radarPayload);
    rows.forEach(function (row) {
      var tr = document.createElement("tr");
      tr.appendChild(brandCell(row, t("radar.colBrand")));
      tr.appendChild(textCell(publicHandle(row) || "—", t("radar.colAccount"), false));
      tr.appendChild(textCell(shownNumber(row, "x_followers", formatInt), t("radar.colFollowers"), true));
      tr.appendChild(textCell(shownNumber(row, "x_mentions_7d", formatInt), t("radar.colMentions"), true));
      tr.appendChild(heatCell(row, t("radar.colHeat")));
      body.appendChild(tr);
    });
  }

  function applyLang(next) {
    lang = next === "zh" || next === "en" ? next : "id";
    document.documentElement.lang = lang === "zh" ? "zh-CN" : lang;
    document.title = t("meta.title");
    var desc = document.querySelector('meta[name="description"]');
    if (desc) desc.setAttribute("content", t("meta.description"));
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      el.textContent = t(el.getAttribute("data-i18n"));
    });
    document.querySelectorAll("[data-i18n-aria]").forEach(function (el) {
      el.setAttribute("aria-label", t(el.getAttribute("data-i18n-aria")));
    });
    document.querySelectorAll("[data-mail]").forEach(function (el) {
      el.setAttribute("href", mailto(el.getAttribute("data-mail")));
    });
    document.querySelectorAll("[data-set-lang]").forEach(function (btn) {
      var on = btn.getAttribute("data-set-lang") === lang;
      btn.setAttribute("aria-pressed", on ? "true" : "false");
      btn.classList.toggle("is-on", on);
    });
    renderRadar();
  }

  function readLang() {
    try {
      var saved = localStorage.getItem(KEY);
      if (saved === "id" || saved === "zh" || saved === "en") return saved;
    } catch (err) {
      return "id";
    }
    return "id";
  }

  function checkPacks() {
    var keys = Object.keys(STR.id);
    ["zh", "en"].forEach(function (code) {
      keys.forEach(function (key) {
        if (!Object.prototype.hasOwnProperty.call(STR[code], key)) {
          throw new Error("missing " + code + " " + key);
        }
      });
      Object.keys(STR[code]).forEach(function (key) {
        if (!Object.prototype.hasOwnProperty.call(STR.id, key)) {
          throw new Error("extra " + code + " " + key);
        }
      });
    });
    ["id", "zh", "en"].forEach(function (code) {
      if (!MAILTO[code].compare || !MAILTO[code].supplier) {
        throw new Error("missing mailto " + code);
      }
    });
  }

  checkPacks();
  if (typeof document === "undefined") return;

  applyLang(readLang());
  document.querySelectorAll("[data-set-lang]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var next = btn.getAttribute("data-set-lang");
      try { localStorage.setItem(KEY, next); } catch (err) { /* private mode */ }
      applyLang(next);
    });
  });

  fetch(RADAR_URL, { headers: { Accept: "application/json" } })
    .then(function (res) {
      if (!res.ok) throw new Error("radar");
      return res.json();
    })
    .then(function (data) {
      if (!data || !Array.isArray(data.brands)) throw new Error("radar");
      radarPayload = data;
      radarFailed = false;
      renderRadar();
    })
    .catch(function () {
      radarFailed = true;
      radarPayload = null;
      renderRadar();
    });
})();
