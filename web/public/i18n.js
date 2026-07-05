const dict = {
    en: {
        title: "US Sector & Theme Rotation Tracker",
        rrg_title: "Relative Rotation Graph",
        filter_theme: "Theme",
        filter_sector: "Sector ETF",
        filter_all: "All",
        rrg_legend: "X = RS-Ratio (Current strength vs Market) • Y = RS-Momentum (Momentum of strength) • Green = Leading • Blue = Improving • Yellow = Weakening • Red = Lagging • Large dot = latest week",
        heatmap_title: "Heatmap Returns (equal-weight)",
        heatmap_note: "* Based on Yahoo Finance daily close",
        col_theme: "Theme / Sector",
        col_zone: "Zone",
        playbook_title: "Momentum Playbook",
        pb_leading_title: "Leading — Strong & Accelerating",
        pb_leading_desc: "Outperforming market and momentum is accelerating. Wait for pullback to enter.",
        pb_improving_title: "Improving — Best Risk/Reward",
        pb_improving_desc: "Underperforming but momentum has shifted positive. Best entry point.",
        pb_weakening_title: "Weakening — Take Profits",
        pb_weakening_desc: "Outperforming but momentum is slowing. Look to take profits.",
        pb_lagging_title: "Lagging — Avoid",
        pb_lagging_desc: "Underperforming and momentum is negative. Avoid entirely.",
        pb_legend: "Badge = Breadth health (Green ≥50% above 20DMA • Yellow 30-50% • Red <30% • Gray = ETF). Sorted by 1M vs SPY.",
        breadth_title: "Breadth & Volume",
        col_breadth_bar: "% Above 20DMA",
        col_vol: "Dollar Vol Ratio (5D/20D)",
        appendix_title: "Appendix",
        disclaimer: "This dashboard is for educational and observational purposes only. It is not investment advice or a recommendation to buy/sell any security. Calculations use equal-weight baskets, which may differ from real ETFs (market-cap weighted). Investing involves risk; consult a licensed professional before making decisions.",
        footer_note: "Note: Data is automatically updated daily after US market close.",
        col_constituents: "Constituents: ",
        data_incomplete: "Incomplete Data",
        // ─── New keys: period selector / ETF mode ───
        periods_max: "Select 4 periods maximum.",
        etfs_max: "Select 20 ETFs maximum.",
        view_themes: "View: Themes",
        view_etfs: "View: ETFs",
        select_etfs_title: "Select ETFs (max 20)",
        etfs_selected: (n) => `${n} / 20 ETFs selected`,
        reset_to_default: "Reset to default",
        clear_all: "Clear all",
        etf_search_placeholder: "Search ETF by ticker or name...",
        etf_min_one: "Select at least 1 ETF.",
        etf_name_label: "ETF",
        vs_spy_suffix: "vs SPY",
        // ─── Feedback feature ───
        feedback_btn: "Feedback",
        feedback_title: "Send Feedback / Feature Request",
        feedback_intro: "Spotted a bug? Have an idea? Let me know.",
        feedback_requestor: "Nickname",
        feedback_details: "Details",
        feedback_photo: "Attach photo (optional)",
        feedback_email: "Email (optional — only seen by admin, never public)",
        feedback_submit: "Send",
        feedback_sending: "Sending...",
        feedback_success: "Thanks! Your feedback was sent. The admin will review it.",
        feedback_error: "Something went wrong. Please try again or email directly.",
        feedback_public_title: "Feedback & Feature Requests",
        feedback_public_intro: "Public log of submitted feedback. Email addresses are kept private.",
        feedback_col_requestor: "Requestor",
        feedback_col_details: "Details",
        feedback_col_picture: "Picture",
        feedback_status_open: "open",
        feedback_status_progress: "in progress",
        feedback_status_done: "done",
        feedback_empty: "No feedback yet. Be the first to send some!"
    },
    th: {
        title: "US Sector & Theme Rotation Tracker",
        rrg_title: "Relative Rotation Graph (เทียบ SPY, หางย้อนหลัง 8 สัปดาห์)",
        filter_theme: "ธีม",
        filter_sector: "Sector ETF",
        filter_all: "ทั้งหมด",
        rrg_legend: "แกน X = RS-Ratio (แรงเทียบตลาดปัจจุบัน) • แกน Y = RS-Momentum (โมเมนตัมของแรงนั้น) • เขียว Leading = แข็งและยังแรงขึ้น • ฟ้า Improving = ยังอ่อนแต่กำลังฟื้น • เหลือง Weakening = ยังแข็งแต่แผ่ว • แดง Lagging = อ่อนและยังแย่ลง • จุดใหญ่คือสัปดาห์ล่าสุด",
        heatmap_title: "Heatmap ผลตอบแทนรายธีม (equal-weight)",
        heatmap_note: "* อ้างอิงจากราคาปิดสิ้นวันของ Yahoo Finance",
        col_theme: "ธีม / Sector",
        col_zone: "โซน",
        playbook_title: "Momentum Playbook — เล่นตาม rotation ยังไง",
        pb_leading_title: "Leading — ถือต่อ / เล่นโมเมนตัม",
        pb_leading_desc: "กลุ่มที่แข็งกว่าตลาดและยังแรงขึ้น เหมาะสำหรับสาย momentum แต่ต้องดู RS-Momentum ถ้าเริ่มโค้งลงใกล้ 100 แปลว่ากำลังจะเป็น Weakening ให้เตรียมแผนออก",
        pb_improving_title: "Improving — จุดเข้าที่ risk/reward ดีสุด",
        pb_improving_desc: "ยังอ่อนกว่าตลาดแต่โมเมนตัมกลับทิศแล้ว คือ 'เงินเริ่มไหลเข้าแต่ราคายังไม่แพง' สายซื้อก่อนฝูงชนเล่นตรงนี้",
        pb_weakening_title: "Weakening — ทยอยขาย ห้ามเพิ่มไม้",
        pb_weakening_desc: "ยังแข็งกว่าตลาดอยู่ แต่แรงส่งแผ่วลง คือโซนที่คนติดดอยเยอะสุดเพราะ 'ผลตอบแทนสะสมยังสวย' ถ้าจะช้อนให้รอม้วนวงลง Lagging แล้วกลับขึ้น Improving ก่อน",
        pb_lagging_title: "Lagging — ห้ามรับช้อน",
        pb_lagging_desc: "อ่อนกว่าตลาดและยังแย่ลง ข้ามไปเลย เด้งแรงรายสัปดาห์ในโซนนี้ส่วนใหญ่คือ dead cat bounce จะน่าสนใจก็ต่อเมื่อขยับข้ามขึ้นไป Improving เท่านั้น",
        pb_legend: "ขอบสีของป้าย = สุขภาพ breadth (เขียว ≥50% ของสมาชิกยืนเหนือ 20DMA • เหลือง 30-50% • แดง <30% • เทา = Sector ETF ไม่มีค่า breadth) ตัวเลข B คือ % สมาชิกเหนือ 20DMA • วงจรปกติหมุนตามเข็มนาฬิกา: Improving → Leading → Weakening → Lagging",
        breadth_title: "Breadth & Volume — สัญญาณเตือนก่อนราคา",
        col_breadth_bar: "% สมาชิกเหนือ 20DMA",
        col_vol: "Dollar Vol Ratio (5D/20D)",
        appendix_title: "Appendix — จะเล่นธีมไหน ไปตัวไหนได้บ้าง",
        disclaimer: "ข้อมูลบนหน้านี้เป็นเครื่องมือเพื่อการศึกษาและสังเกตการณ์เท่านั้น ไม่ใช่คำแนะนำการลงทุนหรือคำแนะนำซื้อขายรายตัว การคำนวณใช้ตะกร้าแบบ equal-weight ซึ่งอาจต่างจาก ETF จริงที่ถ่วงตาม market cap การลงทุนมีความเสี่ยง ผู้ลงทุนควรศึกษาข้อมูลและปรึกษาผู้เชี่ยวชาญที่มีใบอนุญาตก่อนตัดสินใจ",
        footer_note: "ข้อควรรู้: ข้อมูลอัปเดตอัตโนมัติวันละครั้งหลังตลาดสหรัฐปิด",
        col_constituents: "หุ้นในตะกร้า: ",
        data_incomplete: "ข้อมูลไม่ครบ",
        // ─── New keys: period selector / ETF mode ───
        periods_max: "เลือกได้สูงสุด 4 ช่วงเวลา",
        etfs_max: "เลือก ETF ได้สูงสุด 20 ตัว",
        view_themes: "มุมมอง: ธีม",
        view_etfs: "มุมมอง: ETF",
        select_etfs_title: "เลือก ETF (สูงสุด 20)",
        etfs_selected: (n) => `เลือกแล้ว ${n} / 20 ETF`,
        reset_to_default: "คืนค่าเริ่มต้น",
        clear_all: "ล้างทั้งหมด",
        etf_search_placeholder: "ค้นหา ETF ตามรหัสหรือชื่อ...",
        etf_min_one: "เลือก ETF อย่างน้อย 1 ตัว",
        etf_name_label: "ETF",
        vs_spy_suffix: "เทียบ SPY",
        // ─── Feedback feature ───
        feedback_btn: "ส่งความคิดเห็น",
        feedback_title: "ส่งความคิดเห็น / คำขอฟีเจอร์",
        feedback_intro: "เจอบั๊ก? มีไอเดีย? บอกเราได้เลย",
        feedback_requestor: "ชื่อเล่น",
        feedback_details: "รายละเอียด",
        feedback_photo: "แนบรูป (ไม่บังคับ)",
        feedback_email: "อีเมล (ไม่บังคับ — ผู้ดูแลเท่านั้นที่เห็น, ไม่เผยแพร่)",
        feedback_submit: "ส่ง",
        feedback_sending: "กำลังส่ง...",
        feedback_success: "ขอบคุณ! ความคิดเห็นของคุณถูกส่งแล้ว ผู้ดูแลจะตรวจสอบ",
        feedback_error: "ส่งไม่สำเร็จ ลองอีกครั้งหรือส่งอีเมลตรงๆ",
        feedback_public_title: "ความคิดเห็น & คำขอฟีเจอร์",
        feedback_public_intro: "บันทึกความคิดเห็นที่ส่งเข้ามา (อีเมลเก็บส่วนตัว ไม่เผยแพร่)",
        feedback_col_requestor: "ผู้ส่ง",
        feedback_col_details: "รายละเอียด",
        feedback_col_picture: "รูป",
        feedback_status_open: "เปิด",
        feedback_status_progress: "กำลังทำ",
        feedback_status_done: "เสร็จแล้ว",
        feedback_empty: "ยังไม่มีความคิดเห็น เป็นคนแรกที่ส่งได้เลย!"
    }
};

let currentLang = localStorage.getItem('lang') || 'en';

function applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (dict[currentLang] && dict[currentLang][key]) {
            el.innerText = dict[currentLang][key];
        }
    });
}

function toggleLang() {
    currentLang = currentLang === 'th' ? 'en' : 'th';
    localStorage.setItem('lang', currentLang);
    applyTranslations();
    document.dispatchEvent(new Event('langChanged'));
}

document.addEventListener('DOMContentLoaded', () => {
    applyTranslations();
    document.getElementById('langToggle').addEventListener('click', toggleLang);
});
