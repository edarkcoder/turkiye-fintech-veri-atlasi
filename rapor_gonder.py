"""
Günlük BIST Raporu - Notebook çalıştırıcı ve e-mail gönderici
"""

import subprocess
import json
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# ─── Ayarlar ────────────────────────────────────────────────────────────────

NOTEBOOKS = [
    ("bist_hacim_tarayici.ipynb",       "📊 BIST Hacim Tarayıcı"),
    ("bist_hacim_tarayici_referans.ipynb", "📋 BIST Hacim Referans"),
    ("bist_mum_formasyonu_tarayici.ipynb", "🕯️ Mum Formasyonu Tarayıcı"),
    ("turkiye_ekonomik_takvim.ipynb",   "🗓️ Ekonomik Takvim"),
]

EMAIL_FROM     = os.environ["EMAIL_FROM"]
EMAIL_TO       = os.environ["EMAIL_TO"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]

# ─── Notebook çalıştır, çıktıları topla ─────────────────────────────────────

def notebook_calistir(dosya_adi):
    """Notebook'u çalıştırıp metin çıktılarını döndür."""
    cikti_dosyasi = dosya_adi.replace(".ipynb", "_output.ipynb")
    
    sonuc = subprocess.run(
        [
            "jupyter", "nbconvert",
            "--to", "notebook",
            "--execute",
            "--output", cikti_dosyasi,
            "--ExecutePreprocessor.timeout=120",
            dosya_adi,
        ],
        capture_output=True,
        text=True,
    )

    if sonuc.returncode != 0:
        return f"❌ Hata:\n{sonuc.stderr[:500]}"

    # Çalıştırılan notebook'tan metin çıktılarını çek
    with open(cikti_dosyasi, encoding="utf-8") as f:
        nb = json.load(f)

    satirlar = []
    for cell in nb.get("cells", []):
        for output in cell.get("outputs", []):
            if output.get("output_type") in ("stream", "execute_result"):
                text = output.get("text", output.get("data", {}).get("text/plain", ""))
                if isinstance(text, list):
                    text = "".join(text)
                satirlar.append(text.strip())

    return "\n".join(satirlar) if satirlar else "(Çıktı yok)"


# ─── HTML e-mail oluştur ─────────────────────────────────────────────────────

def html_olustur(bolumler):
    tarih = datetime.now().strftime("%d %B %Y, %A")
    
    bolum_html = ""
    for baslik, icerik in bolumler:
        bolum_html += f"""
        <div style="margin-bottom:28px;">
          <h2 style="color:#1a1a2e;border-bottom:2px solid #e63946;padding-bottom:6px;margin-bottom:12px;">
            {baslik}
          </h2>
          <pre style="background:#f8f9fa;border-left:4px solid #457b9d;padding:14px;
                      font-family:monospace;font-size:13px;line-height:1.6;
                      white-space:pre-wrap;word-wrap:break-word;border-radius:4px;">
{icerik}
          </pre>
        </div>
        """

    return f"""
    <html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;padding:24px;color:#333;">
      <div style="background:#1a1a2e;color:white;padding:20px 24px;border-radius:8px 8px 0 0;">
        <h1 style="margin:0;font-size:20px;">📈 Günlük BIST Raporu</h1>
        <p style="margin:6px 0 0;opacity:0.8;font-size:14px;">{tarih}</p>
      </div>
      <div style="border:1px solid #ddd;border-top:none;padding:24px;border-radius:0 0 8px 8px;">
        {bolum_html}
        <p style="font-size:12px;color:#999;margin-top:24px;border-top:1px solid #eee;padding-top:12px;">
          Bu rapor GitHub Actions tarafından otomatik oluşturulmuştur.<br>
          Kaynak: turkiye-fintech-veri-atlasi
        </p>
      </div>
    </body></html>
    """


# ─── E-mail gönder ───────────────────────────────────────────────────────────

def email_gonder(html_icerik):
    tarih = datetime.now().strftime("%d.%m.%Y")
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📈 Günlük BIST Raporu — {tarih}"
    msg["From"]    = EMAIL_FROM
    msg["To"]      = EMAIL_TO
    
    msg.attach(MIMEText(html_icerik, "html", "utf-8"))
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    
    print(f"✅ E-mail gönderildi → {EMAIL_TO}")


# ─── Ana akış ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    bolumler = []
    
    for dosya, baslik in NOTEBOOKS:
        print(f"⏳ Çalıştırılıyor: {baslik}")
        icerik = notebook_calistir(dosya)
        bolumler.append((baslik, icerik))
        print(f"✅ Tamamlandı: {baslik}\n")
    
    html = html_olustur(bolumler)
    email_gonder(html)
