# US Sector & Theme Rotation Tracker

แดชบอร์ดสำหรับติดตามการหมุนเวียนของเงินทุนในตลาดหุ้นสหรัฐ (Sector & Theme Rotation) ผ่านกราฟ Relative Rotation Graph (RRG) และ Heatmap แบบรายวัน 

เครื่องมือนี้คำนวณข้อมูลแบบ **Equal-weight** เป็นหลัก เพื่อดูทิศทางของ "กลุ่ม" โดยไม่ถูกบิดเบือนจากหุ้นยักษ์ใหญ่เพียงไม่กี่ตัว 

> **คำเตือน:** ข้อมูลบนหน้านี้เป็นเครื่องมือเพื่อการศึกษาและสังเกตการณ์เท่านั้น ไม่ใช่คำแนะนำการลงทุนหรือคำแนะนำซื้อขายรายตัว

## วิธีติดตั้งและรันบนเครื่องตัวเอง (Local Development)

โปรเจกต์นี้ถูกออกแบบมาให้เรียบง่ายที่สุดโดยไม่ต้องใช้ Database หรือ Backend server ซับซ้อน การคำนวณทั้งหมดทำผ่าน Python script และได้ผลลัพธ์เป็นไฟล์ `data.json` เดี่ยวๆ สำหรับให้เว็บ (HTML/CSS/JS) นำไปแสดงผล

### สิ่งที่ต้องมี
- Python 3.11 หรือใหม่กว่า
- Git

### ขั้นตอนการรัน

1. **โคลนโปรเจกต์ลงมาที่เครื่อง:**
   ```bash
   git clone <repo-url>
   cd Rotation
   ```

2. **สร้างและเปิดใช้งาน Virtual Environment:**
   ```bash
   # สำหรับ Mac/Linux:
   python -m venv .venv
   source .venv/bin/activate

   # สำหรับ Windows:
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **ติดตั้ง Library ที่จำเป็น:**
   ```bash
   pip install -r requirements.txt
   ```

4. **ดึงข้อมูลราคาและคำนวณผลลัพธ์:**
   ```bash
   python -m pipeline.run
   ```
   *คำสั่งนี้จะไปดึงราคาหุ้นย้อนหลังจาก Yahoo Finance แล้วคำนวณค่าต่างๆ (RRG, ผลตอบแทน, Breadth) จากนั้นบันทึกผลลงในโฟลเดอร์ `web/public/data.json`*

5. **เปิดหน้าเว็บเพื่อดูผลลัพธ์:**
   ```bash
   cd web/public
   python -m http.server 8000
   ```
   *เปิดเบราว์เซอร์แล้วเข้าไปที่ `http://localhost:8000`*

### การรัน Unit Test
เพื่อตรวจสอบความถูกต้องของสูตรคำนวณ สามารถรันคำสั่ง:
```bash
pytest
```

## สถาปัตยกรรม (Architecture)
โปรเจกต์นี้ใช้ GitHub Actions ในการดึงข้อมูลและอัปเดตไฟล์ `data.json` โดยอัตโนมัติทุกวันหลังตลาดสหรัฐปิดทำการ และใช้ GitHub Pages ในการโฮสต์หน้าเว็บ ทำให้ไม่มีค่าใช้จ่ายในการดูแลระบบ (100% Free)
