/* Language switch for the draft privacy and terms pages.
   Same browser key as the homepage. No network requests. */
(function () {
  var KEY = "nbo-public-lang";
  var lang = "id";

  var STR = {
    id: {
      "skip": "Langsung ke isi",
      "lang.group": "Bahasa",
      "lang.nav": "Navigasi",
      "draft.badge": "Draf",
      "footer.note": "PT XDirection Public Relations · Nusantara Brand OS",
      "footer.home": "Beranda",
      "footer.privacy": "Kebijakan privasi",
      "footer.terms": "Ketentuan layanan",
      "privacy.metaTitle": "Kebijakan privasi (draf) · Nusantara Brand OS",
      "privacy.metaDescription": "Draf kebijakan privasi Nusantara Brand OS, dioperasikan oleh PT XDirection Public Relations.",
      "privacy.kicker": "Kebijakan privasi",
      "privacy.title": "Kebijakan privasi",
      "privacy.draft": "Teks ini adalah draf. Ini bukan dokumen hukum yang sudah final, dan tidak menafsirkan pasal undang-undang.",
      "privacy.whoTitle": "Siapa yang mengoperasikan",
      "privacy.whoBody": "Nusantara Brand OS dioperasikan oleh PT XDirection Public Relations, perusahaan Indonesia.",
      "privacy.contactTitle": "Kontak",
      "privacy.contactBody": "Satu-satunya saluran di situs ini adalah email ptxdirectionpublicrelations@gmail.com. Situs ini tidak menampilkan nomor telepon. Tidak ada formulir yang disimpan di server. Tautan email membuka aplikasi email pengunjung.",
      "privacy.sourcesTitle": "Dari mana data berasal",
      "privacy.publicTitle": "Data media sosial publik",
      "privacy.publicBody": "Contoh radar di situs ini membaca berkas data. Angka yang ditampilkan adalah angka yang berkas itu tandai sebagai data publik X, bersama catatan sumber dan tanggal yang ada di berkas. Instagram dan TikTok belum terhubung di situs ini, jadi angka kedua platform tidak ditampilkan.",
      "privacy.authTitle": "Data yang diberi kuasa oleh merek",
      "privacy.authBody": "Jika suatu merek memberi kuasa kepada kami untuk menyimpan data, data itu dipakai untuk tujuan yang diberi kuasa.",
      "privacy.withdrawTitle": "Menarik kuasa dan menghapus data",
      "privacy.withdrawBody": "Pemberi kuasa dapat menarik kuasa kapan saja dengan mengirim email ke alamat di atas. Setelah permintaan diterima, kami menghapus data yang kami simpan berdasarkan kuasa tersebut.",
      "privacy.publicRemoveBody": "Jika suatu merek meminta agar data media sosial publiknya tidak lagi ditampilkan di situs ini, kami menghapus tampilan itu dari situs ini. Kami tidak menguasai unggahan asli di platform asalnya.",
      "privacy.browserTitle": "Pilihan bahasa di peramban",
      "privacy.browserBody": "Pilihan bahasa disimpan di peramban pengunjung dan tidak dikirim kepada kami.",
      "privacy.lawTitle": "Rujukan",
      "privacy.lawBody": "Kami merujuk Undang-Undang Nomor 27 Tahun 2022 tentang Pelindungan Data Pribadi (UU 27/2022). Draf ini tidak menjelaskan pasal-pasal undang-undang itu, dan bukan pernyataan bahwa suatu sertifikasi atau pemeriksaan telah selesai.",
      "terms.metaTitle": "Ketentuan layanan (draf) · Nusantara Brand OS",
      "terms.metaDescription": "Draf ketentuan layanan Nusantara Brand OS, dioperasikan oleh PT XDirection Public Relations.",
      "terms.kicker": "Ketentuan layanan",
      "terms.title": "Ketentuan layanan",
      "terms.draft": "Teks ini adalah draf ketentuan layanan. Ini bukan perjanjian yang sudah final, dan tidak menafsirkan pasal undang-undang.",
      "terms.whoTitle": "Siapa yang mengoperasikan",
      "terms.whoBody": "Situs ini dioperasikan oleh PT XDirection Public Relations, perusahaan Indonesia. Kontak hanya lewat email ptxdirectionpublicrelations@gmail.com.",
      "terms.scopeTitle": "Apa yang ada di situs ini",
      "terms.brandBody": "Untuk merek: radar panas yang angkanya diambil dari data publik yang ditandai di berkas data, dan pengajuan perbandingan kompetitor satu halaman lewat email. Pengajuan itu gratis. Pengelolaan media sosial, pustaka materi, dan layanan pelanggan berbasis AI belum dibuka dan belum menerima permintaan.",
      "terms.supplierBody": "Untuk pemasok: biji kopi, teh, bahan baku, peralatan, dan kemasan dapat diajukan lewat email. Pada tahap awal, pendaftaran gratis. Situs publik ini tidak menuliskan tarif.",
      "terms.requestBody": "Email yang dibuka dari situs ini adalah permintaan. Permintaan itu belum menjadi kerja sama, sampai ada kesepakatan terpisah.",
      "terms.radarBody": "Angka pada contoh radar adalah data yang berkas tandai sebagai data publik X, bersama catatan sumber dan tanggal di berkas itu. Situs ini tidak menjanjikan hasil usaha dari angka tersebut.",
      "terms.dataTitle": "Data dan penarikan kuasa",
      "terms.dataBody": "Uraian data ada di kebijakan privasi. Pemberi kuasa dapat menarik kuasa kapan saja lewat email, dan kami menghapus data yang kami simpan berdasarkan kuasa itu. Data media sosial publik yang diminta untuk tidak ditampilkan akan dihapus dari situs ini.",
      "terms.lawBody": "Untuk data pribadi, kami merujuk Undang-Undang Nomor 27 Tahun 2022 tentang Pelindungan Data Pribadi (UU 27/2022). Draf ini tidak menjelaskan pasal-pasalnya."
    },
    zh: {
      "skip": "跳到正文",
      "lang.group": "语言",
      "lang.nav": "导航",
      "draft.badge": "草稿",
      "footer.note": "PT XDirection Public Relations · Nusantara Brand OS",
      "footer.home": "首页",
      "footer.privacy": "隐私政策",
      "footer.terms": "服务条款",
      "privacy.metaTitle": "隐私政策（草稿）· Nusantara Brand OS",
      "privacy.metaDescription": "Nusantara Brand OS 隐私政策草稿。运营主体为 PT XDirection Public Relations。",
      "privacy.kicker": "隐私政策",
      "privacy.title": "隐私政策",
      "privacy.draft": "本文是草稿，不是已经定稿的法律文件，也不逐条解释法律。",
      "privacy.whoTitle": "运营主体",
      "privacy.whoBody": "Nusantara Brand OS 由印尼公司 PT XDirection Public Relations 运营。",
      "privacy.contactTitle": "联系",
      "privacy.contactBody": "本站只使用邮箱 ptxdirectionpublicrelations@gmail.com。本站不放电话号码。没有保存在服务器上的表单。邮件链接会在访问者自己的邮件程序里打开。",
      "privacy.sourcesTitle": "数据来源",
      "privacy.publicTitle": "公开社媒数据",
      "privacy.publicBody": "本站的雷达样例读取数据文件。页面展示的数字，是该文件标为 X 公开数据的数字，并附有文件中的来源说明和日期。Instagram 与 TikTok 尚未接通，因此不展示这两个平台的数字。",
      "privacy.authTitle": "品牌授权数据",
      "privacy.authBody": "如果品牌授权我们保存数据，这些数据只用于所授权的用途。",
      "privacy.withdrawTitle": "撤回授权与删除数据",
      "privacy.withdrawBody": "授权方可以随时向上述邮箱发送邮件，撤回授权。我们收到请求后，删除我们基于该授权保存的数据。",
      "privacy.publicRemoveBody": "如果品牌要求本站不再展示其公开社媒数据，我们会从本站删除该展示。我们不能控制原始平台上的公开帖文。",
      "privacy.browserTitle": "浏览器中的语言选择",
      "privacy.browserBody": "语言选择保存在访问者的浏览器里，不会发送给我们。",
      "privacy.lawTitle": "参照",
      "privacy.lawBody": "我们参照印度尼西亚个人数据保护法，即 2022 年第 27 号法律（UU 27/2022）。本草稿不解释该法的具体条款，也不是已经完成认证或审查的声明。",
      "terms.metaTitle": "服务条款（草稿）· Nusantara Brand OS",
      "terms.metaDescription": "Nusantara Brand OS 服务条款草稿。运营主体为 PT XDirection Public Relations。",
      "terms.kicker": "服务条款",
      "terms.title": "服务条款",
      "terms.draft": "本文是服务条款草稿，不是已经定稿的协议，也不逐条解释法律。",
      "terms.whoTitle": "运营主体",
      "terms.whoBody": "本站由印尼公司 PT XDirection Public Relations 运营。联系只使用邮箱 ptxdirectionpublicrelations@gmail.com。",
      "terms.scopeTitle": "本站现在提供什么",
      "terms.brandBody": "品牌端：热度雷达使用数据文件中标为公开数据的数字；一页纸竞品对比通过邮件申请，申请免费。社媒代运营、素材库和 AI 客服尚未开通，目前不接受委托。",
      "terms.supplierBody": "供应商端：咖啡豆、茶叶、原料、设备和包材可以通过邮件申请入驻。起步阶段免费入驻。这个公开网站不写收费金额。",
      "terms.requestBody": "从本站打开的邮件是一项申请。在另行达成约定之前，申请本身还不是合作。",
      "terms.radarBody": "雷达样例中的数字，是数据文件标为 X 公开数据的数字，并带有文件中的来源说明和日期。本站不根据这些数字承诺经营结果。",
      "terms.dataTitle": "数据与撤回授权",
      "terms.dataBody": "数据说明见隐私政策。授权方可以随时通过邮件撤回授权，我们删除基于该授权保存的数据。如果要求不再展示公开社媒数据，我们会从本站删除该展示。",
      "terms.lawBody": "关于个人数据，我们参照 2022 年第 27 号法律（UU 27/2022）。本草稿不解释该法的具体条款。"
    },
    en: {
      "skip": "Skip to content",
      "lang.group": "Language",
      "lang.nav": "Navigation",
      "draft.badge": "Draft",
      "footer.note": "PT XDirection Public Relations · Nusantara Brand OS",
      "footer.home": "Home",
      "footer.privacy": "Privacy policy",
      "footer.terms": "Terms of service",
      "privacy.metaTitle": "Privacy policy (draft) · Nusantara Brand OS",
      "privacy.metaDescription": "Draft privacy policy for Nusantara Brand OS, operated by PT XDirection Public Relations.",
      "privacy.kicker": "Privacy policy",
      "privacy.title": "Privacy policy",
      "privacy.draft": "This text is a draft. It is not a final legal document, and it does not interpret individual provisions of any statute.",
      "privacy.whoTitle": "Who operates this site",
      "privacy.whoBody": "Nusantara Brand OS is operated by PT XDirection Public Relations, an Indonesian company.",
      "privacy.contactTitle": "Contact",
      "privacy.contactBody": "The only channel on this site is the email address ptxdirectionpublicrelations@gmail.com. This site does not show a phone number. No form is stored on a server. An email link opens in the visitor's own email app.",
      "privacy.sourcesTitle": "Where data comes from",
      "privacy.publicTitle": "Public social-media data",
      "privacy.publicBody": "The radar sample on this site reads a data file. The figures shown are those the file marks as public X data, together with the source note and date in that file. Instagram and TikTok are not connected on this site, so figures from those platforms are not shown.",
      "privacy.authTitle": "Data a brand authorizes",
      "privacy.authBody": "If a brand authorizes us to keep data, that data is used for the purpose covered by the authorization.",
      "privacy.withdrawTitle": "Withdrawing authorization and deleting data",
      "privacy.withdrawBody": "The person who gave authorization may withdraw it at any time by emailing the address above. After the request is received, we delete the data we hold on the basis of that authorization.",
      "privacy.publicRemoveBody": "If a brand asks us not to show its public social-media data on this site, we remove that display from this site. We do not control the original posts on the source platform.",
      "privacy.browserTitle": "Language choice in the browser",
      "privacy.browserBody": "The language choice is stored in the visitor's browser and is not sent to us.",
      "privacy.lawTitle": "Reference",
      "privacy.lawBody": "We refer to Law Number 27 of 2022 on Personal Data Protection (UU 27/2022). This draft does not explain individual provisions of that law, and it is not a statement that a certification or audit has been completed.",
      "terms.metaTitle": "Terms of service (draft) · Nusantara Brand OS",
      "terms.metaDescription": "Draft terms of service for Nusantara Brand OS, operated by PT XDirection Public Relations.",
      "terms.kicker": "Terms of service",
      "terms.title": "Terms of service",
      "terms.draft": "This text is a draft of the terms of service. It is not a final agreement, and it does not interpret individual provisions of any statute.",
      "terms.whoTitle": "Who operates this site",
      "terms.whoBody": "This site is operated by PT XDirection Public Relations, an Indonesian company. Contact is only by email at ptxdirectionpublicrelations@gmail.com.",
      "terms.scopeTitle": "What this site offers now",
      "terms.brandBody": "For brands: a heat radar whose figures come from data the file marks as public, and a one-page competitor comparison requested by email. That request is free of charge. Social media management, an asset library, and AI customer service are not open and are not taking requests.",
      "terms.supplierBody": "For suppliers: coffee beans, tea, ingredients, equipment, and packaging can be submitted by email. At this early stage, listing is free of charge. This public site does not state fee amounts.",
      "terms.requestBody": "An email opened from this site is a request. The request is not yet a working relationship until there is a separate agreement.",
      "terms.radarBody": "Figures in the radar sample are data the file marks as public X data, with the source note and date in that file. This site does not promise a business result from those figures.",
      "terms.dataTitle": "Data and withdrawal",
      "terms.dataBody": "Data is described in the privacy policy. Authorization may be withdrawn at any time by email, and we delete the data we hold on the basis of that authorization. Public social-media data that we are asked not to show is removed from this site.",
      "terms.lawBody": "For personal data, we refer to Law Number 27 of 2022 (UU 27/2022). This draft does not explain its individual provisions."
    }
  };

  function t(key) {
    var pack = STR[lang] || STR.id;
    if (Object.prototype.hasOwnProperty.call(pack, key)) return pack[key];
    if (Object.prototype.hasOwnProperty.call(STR.id, key)) return STR.id[key];
    return key;
  }

  function applyLang(next) {
    lang = next === "zh" || next === "en" ? next : "id";
    document.documentElement.lang = lang === "zh" ? "zh-CN" : lang;
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var value = t(el.getAttribute("data-i18n"));
      if (el.tagName === "META") el.setAttribute("content", value);
      else el.textContent = value;
    });
    document.querySelectorAll("[data-i18n-aria]").forEach(function (el) {
      el.setAttribute("aria-label", t(el.getAttribute("data-i18n-aria")));
    });
    document.querySelectorAll("[data-set-lang]").forEach(function (btn) {
      var on = btn.getAttribute("data-set-lang") === lang;
      btn.setAttribute("aria-pressed", on ? "true" : "false");
      btn.classList.toggle("is-on", on);
    });
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
})();
