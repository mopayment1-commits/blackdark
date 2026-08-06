# تشغيل BLACKDARK محليًا على Windows (بدون بطاقة)

## أمر واحد بعد ما الإعداد خلص

في PowerShell جوه مجلد المشروع (ومفعّل `.venv`):

```powershell
python run_service.py web
```

أو:

```powershell
powershell -File start_local.ps1
```

بعدها افتح: `http://localhost:8080/#oracle`

## مهم

- استخدم **`web`** — مش `all` — عشان الصفحة تفضل شغّالة من غير ما السيرفر يوقف على مراجعة الـ manifest.
- لو الصفحة قالت "This site can't be reached": السيرفر واقف → شغّل الأمر فوق تاني.
- تحذيرات API key / Reddit عادية ومش بتوقف الزر.

## لو الزر كان واقف قبل كده

حدّث ملف الصفحة:

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/mopayment1-commits/blackdark/cursor/fix-landing-oracle-button-eef3/templates/landing.html" -OutFile "templates\landing.html"
```

وقّف السيرفر (Ctrl+C) وشغّله تاني بـ `python run_service.py web` ثم Ctrl+F5 في المتصفح.
