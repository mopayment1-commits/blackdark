# تشغيل BLACKDARK على جهازك (ويندوز) — بدون بطاقة

## قبل ما تبدأ
لازم يكون عندك **Python 3.12**.  
لو مش متأكد: افتح PowerShell واكتب:

```powershell
python --version
```

لو مش ظاهر رقم زي `3.12.x` → نزّل من: https://www.python.org/downloads/  
مهم: أثناء التثبيت علّم ✓ **Add python.exe to PATH**

---

## الخطوات

### 1) حمّل المشروع
افتح: https://github.com/mopayment1-commits/blackdark  
→ زر أخضر **Code** → **Download ZIP**  
→ فك الضغط في مجلد سهل مثل: `C:\blackdark`

### 2) افتح PowerShell في المجلد
داخل مجلد المشروع (اللي فيه `run_service.py`):

```powershell
cd C:\blackdark
```

(غيّر المسار لو حطيته مكان تاني)

### 3) أنشئ بيئة Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

لو ظهر خطأ عن ExecutionPolicy:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### 4) ثبّت المكتبات

```powershell
python -m pip install --upgrade pip
pip install -r requirements-prod.txt
```

### 5) أنشئ ملف `.env`
في نفس المجلد، أنشئ ملف اسمه `.env` وداخله:

```env
ENV=development
SERVICE_MODE=web
SOFT_LAUNCH=true
PRICE_FEED_WS_ONLY=false
LAUNCH_SKIP_TELEGRAM=true
LAUNCH_SKIP_EMAIL=true
```

### 6) شغّل الموقع

```powershell
python run_service.py web --port 8080
```

اترك النافذة مفتوحة.

### 7) افتح المتصفح
http://localhost:8080

جرّب BTC — المفروض **ACT** أو **WAIT** + جملة واضحة.

لإيقاف السيرفر: في PowerShell اضغط `Ctrl+C`.
