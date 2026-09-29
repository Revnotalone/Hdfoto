import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Token Bot dari @BotFather
BOT_TOKEN = "8707206212:AAGyWSodLRtJN2sWx-B9R1b1Q0akC0T9_IE"

def enhance_image(input_path: str, output_path: str):
    """
    Fungsi peng-HD foto menggunakan pemrosesan citra lokal (Pillow & OpenCV):
    1. Upscaling dengan metode Lanczos (menambah resolusi)
    2. Unsharp Masking (menajamkan detail & tekstur)
    3. Noise Reduction (mengurangi bintik/noise)
    4. Color & Contrast Enhancement
    """
    # 1. Buka gambar dengan PIL dan naikkan resolusinya (Upscaling 2x)
    with Image.open(input_path) as img:
        img = img.convert("RGB")
        width, height = img.size
        # Naikkan ukuran 2 kali lipat menggunakan filter Lanczos
        new_size = (width * 2, height * 2)
        upscaled_img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # 2. Penyesuaian Kontras dan Ketajaman Dasar
        enhancer_contrast = ImageEnhance.Contrast(upscaled_img)
        img_contrast = enhancer_contrast.enhance(1.15)  # Naikkan kontras 15%
        
        enhancer_sharpness = ImageEnhance.Sharpness(img_contrast)
        img_sharp = enhancer_sharpness.enhance(1.4)    # Naikkan ketajaman
        
        temp_path = "temp_step1.jpg"
        img_sharp.save(temp_path, quality=95)

    # 3. Lanjutkan pemrosesan dengan OpenCV untuk Unsharp Masking & Denoising
    cv_img = cv2.imread(temp_path)

    # Denoising halus untuk membersihkan noise akibat upscaling
    denoised = cv2.fastNlMeansDenoisingColored(cv_img, None, h=3, hColor=3, templateWindowSize=7, searchWindowSize=21)

    # Unsharp Masking (Teknik penajaman tingkat lanjut)
    gaussian_blur = cv2.GaussianBlur(denoised, (0, 0), 2.0)
    unsharp = cv2.addWeighted(denoised, 1.5, gaussian_blur, -0.5, 0)

    # Simpan hasil akhir
    cv2.imwrite(output_path, unsharp, [int(cv2.IMWRITE_JPEG_QUALITY), 98])

    # Hapus file sementara
    if os.path.exists(temp_path):
        os.remove(temp_path)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk perintah /start"""
    await update.message.reply_text(
        "👋 Selamat datang di **Bot HD Foto**!\n\n"
        "Kirimkan foto (bisa berupa foto biasa atau dikirim sebagai dokumen/file agar kualitas asli terjaga), "
        "dan saya akan menaikkan resolusi serta menajamkan gambarnya secara otomatis murni lewat pemrosesan lokal!"
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler saat pengguna mengirim foto atau dokumen gambar"""
    message = update.message
    status_msg = await message.reply_text("⏳ Sedang memproses dan meningkatkan kualitas foto...")

    input_file_path = "input_temp.jpg"
    output_file_path = "output_hd.jpg"

    try:
        # Ambil file foto dengan ukuran tertinggi
        if message.photo:
            photo_file = await message.photo[-1].get_file()
        elif message.document and message.document.mime_type.startswith("image/"):
            photo_file = await message.document.get_file()
        else:
            await status_msg.edit_text("❌ Mohon kirimkan format gambar yang valid.")
            return

        # Unduh foto dari Telegram
        await photo_file.download_to_drive(input_file_path)

        # Jalankan pemrosesan peningkat kualitas gambar
        enhance_image(input_file_path, output_file_path)

        # Kirim kembali foto yang sudah di-HD kan sebagai dokumen agar tidak terkompresi
        await status_msg.edit_text("📤 Mengirim hasil foto HD...")
        with open(output_file_path, "rb") as doc:
            await message.reply_document(
                document=doc,
                caption="✨ **Foto Berhasil Di-HD-kan!**\n\n• Resolusi ditingkatkan 2x\n• Penajaman tekstur (Unsharp Masking)\n• Penyesuaian kontras & denoising"
            )

        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ Terjadi kesalahan saat memproses foto: {str(e)}")

    finally:
        # Bersihkan file temporer setelah selesai
        for path in [input_file_path, output_file_path]:
            if os.path.exists(path):
                os.remove(path)


def main():
    """Inisialisasi dan jalankan Bot Telegram"""
    app = Application.builder().token(BOT_TOKEN).build()

    # Handler Perintah
    app.add_handler(CommandHandler("start", start_command))

    # Handler Foto & Dokumen Gambar
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_photo))

    print("🤖 Bot Telegram HD Foto berjalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
