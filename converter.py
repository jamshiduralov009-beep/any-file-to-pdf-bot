import os
from PIL import Image
from pypdf import PdfWriter, PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
import docx

def create_pdf_from_text(txt_path, output_pdf_path):
    """Converts a plain text file to PDF."""
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError:
        with open(txt_path, "r", encoding="latin-1", errors="ignore") as f:
            text = f.read()

    doc = SimpleDocTemplate(output_pdf_path, pagesize=A4,
                            rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.leading = 15

    story = []
    lines = text.split("\n")
    for line in lines:
        cleaned_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if cleaned_line.strip() == "":
            story.append(Spacer(1, 10))
        else:
            story.append(Paragraph(cleaned_line, normal_style))

    doc.build(story)
    return output_pdf_path

def create_pdf_from_docx(docx_path, output_pdf_path):
    """Converts DOCX content into a PDF using reportlab."""
    doc_in = docx.Document(docx_path)
    pdf_doc = SimpleDocTemplate(output_pdf_path, pagesize=A4,
                                rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.leading = 15

    heading_style = styles['Heading1']
    heading_style.fontSize = 14
    heading_style.leading = 18

    story = []
    for p in doc_in.paragraphs:
        txt = p.text.strip()
        if not txt:
            story.append(Spacer(1, 8))
            continue
        cleaned = txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if p.style.name.startswith("Heading"):
            story.append(Paragraph(cleaned, heading_style))
            story.append(Spacer(1, 6))
        else:
            story.append(Paragraph(cleaned, normal_style))
            story.append(Spacer(1, 4))

    if not story:
        story.append(Paragraph("(Bo'sh hujjat)", normal_style))

    pdf_doc.build(story)
    return output_pdf_path

def create_pdf_from_image(image_path, output_pdf_path):
    """Converts a single image to a 1-page PDF."""
    with Image.open(image_path) as img:
        img_converted = img.convert('RGB')
        img_converted.save(output_pdf_path, "PDF", resolution=100.0)
    return output_pdf_path

def convert_video_thumbnail_to_pdf(video_path, output_pdf_path):
    """Generates a PDF page showing a snapshot thumbnail of the video."""
    # Attempt frame extraction if cv2/moviepy available, else fallback note
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        success, frame = cap.read()
        cap.release()
        if success:
            temp_img = output_pdf_path + "_thumb.jpg"
            cv2.imwrite(temp_img, frame)
            create_pdf_from_image(temp_img, output_pdf_path)
            if os.path.exists(temp_img):
                os.remove(temp_img)
            return output_pdf_path
    except Exception:
        pass

    # Fallback placeholder PDF for video
    c = canvas.Canvas(output_pdf_path, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Video Fayl Hujjati")
    c.setFont("Helvetica", 12)
    c.drawString(100, 720, f"Fayl nomi: {os.path.basename(video_path)}")
    c.drawString(100, 690, "Eslatma: Video fayllar PDF ichida bevosita ijro etilmaydi.")
    c.save()
    return output_pdf_path

def combine_files_to_single_pdf(file_paths, output_final_pdf):
    """
    Takes a list of file paths (images, txt, docx, pdf, video)
    and merges them into a single coherent PDF document.
    """
    writer = PdfWriter()
    temp_pdfs = []

    try:
        for idx, file_path in enumerate(file_paths):
            ext = os.path.splitext(file_path)[1].lower()
            temp_pdf = f"{output_final_pdf}_part_{idx}.pdf"

            if ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']:
                create_pdf_from_image(file_path, temp_pdf)
                temp_pdfs.append(temp_pdf)
            elif ext in ['.txt', '.log']:
                create_pdf_from_text(file_path, temp_pdf)
                temp_pdfs.append(temp_pdf)
            elif ext in ['.docx']:
                create_pdf_from_docx(file_path, temp_pdf)
                temp_pdfs.append(temp_pdf)
            elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                convert_video_thumbnail_to_pdf(file_path, temp_pdf)
                temp_pdfs.append(temp_pdf)
            elif ext == '.pdf':
                temp_pdfs.append(file_path)
            else:
                # Unsupported format, try converting as plain text
                try:
                    create_pdf_from_text(file_path, temp_pdf)
                    temp_pdfs.append(temp_pdf)
                except Exception:
                    continue

        # Merge all generated PDFs
        for pdf_file in temp_pdfs:
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                writer.add_page(page)

        with open(output_final_pdf, "wb") as f_out:
            writer.write(f_out)

        return output_final_pdf
    finally:
        # Cleanup temporary intermediary PDFs
        for pdf_file in temp_pdfs:
            if pdf_file not in file_paths and os.path.exists(pdf_file):
                try:
                    os.remove(pdf_file)
                except Exception:
                    pass
